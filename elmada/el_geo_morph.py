"""Handles power plant list from Global Energy Observatory via morph."""

import collections
import logging
import sqlite3
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import (Any, Callable, Dict, Iterable, List, Optional, Set, Tuple,
                    Union)

import numpy as np
import pandas as pd
import requests

from elmada import helper as hp
from elmada import mappings as mp
from elmada import paths

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARN)

DB_DIR = paths.CACHE_DIR
DB_FILE_FORMAT = "GEO-database.{filetype}"

CC_WEIGHTING = {
    'Thermal and CCGT': 1,
    'Power and Heat Combined Cycle Gas Turbine': 1,
    'Combined Cycle Gas Engine (CCGE)': 1,
    'Combined Cycle Gas Turbine': 1,
    'OCGT and CCGT': .49,
    'Sub-critical Thermal': 0,
    'Power and Heat Open Cycle Gas Turbine': 0,
    'Open Cycle Gas Turbine': 0,
    'Heat and Power Steam Turbine': 0,
    'Super-critical Thermal': 0,
    'Gas Engines': 0,
    None: 0
}

COLS = {
    "Name": "name",
    "Type": "fuel",
    "Country": "country",
    "Type_of_Plant_rng1": "plant_type",
    "Type_of_Fuel_rng1_Primary": "primary_fuel",
    "Design_Capacity_MWe_nbr": "capa",
    "GEO_Assigned_Identification_Number": "id",
    "Status_of_Plant_itf": "status"
}

NON_OPERATIONAL_STATUSES = [
    "Built and In Test Stage",
    "Decommissioned",
    "Demolished",
    "Design and Planning Stage",
    "Final Bid and Approval Stage",
    "Mothballed Full",
    "Mothballed Partial",
    "Shutdown"
    "Under Construction",
]


@lru_cache(maxsize=1)
def get_installed_capacity(cache: bool = False) -> pd.DataFrame:
    fp = paths.CACHE_DIR / "geo_installed_capacity.h5"

    if cache and fp.exists():
        df = pd.read_hdf(fp)

    else:
        df = get_geo_list()
        df = df.groupby(["cy", "fuel"])["capa"].sum().unstack()
        if cache:
            hp.write_array(df, fp)

    df.index.name = None
    df.columns.name = None
    return df[mp.PWL_FUELS]


@lru_cache(maxsize=1)
def get_pp_sizes(replace_nans_by_mean: bool = True, cache: bool = False) -> pd.DataFrame:
    fp = paths.CACHE_DIR / "ppsizes.h5"

    if cache and fp.exists():
        df = pd.read_hdf(fp)

    else:
        df = get_geo_list()
        df = df.groupby(["cy", "fuel"])["capa"].mean().unstack()
        if cache:
            hp.write_array(df, fp)

    if replace_nans_by_mean:
        logger.info(f"Filled nan's with the following mean values:\n{df.mean()}")
        df = df.fillna(df.mean())
        # these values where filled with mean:
        # df = pd.DataFrame({cy:pwl.prep_installed_generation_capacity(country=cy) for cy in mp.COUNTRIES_FOR_ANALYSIS}).T
        # df[(ge.get_pp_sizes().isna()) & (df>0)].stack()

    return df.astype("int")


def get_ccgt_shares() -> pd.DataFrame:
    geo = get_geo_list()
    valid_countries = get_valid_countries()
    df = pd.DataFrame(index=valid_countries.keys())

    for cy_short, cy_long in valid_countries.items():
        is_gas = geo["fuel"].isin(["gas", "gas_cc"])
        is_country = geo["country"] == cy_long
        geo_sub = geo[is_gas & is_country]
        df.loc[cy_short, "cy_long"] = cy_long
        df.loc[cy_short, "cc_capa"] = geo_sub["capa"] @ geo_sub["cc_weight"]
        df.loc[cy_short, "total_capa"] = geo_sub["capa"].sum()

    df["share_cc"] = df["cc_capa"] / df["total_capa"]
    return df


def get_valid_countries():
    df = get_geo_list()
    avail = set(df["country"].unique())
    d = {short: long for short, long in mp.COUNTRIES_FOR_ANALYSIS.items() if long in avail}
    return collections.OrderedDict(sorted(d.items()))


@lru_cache(maxsize=1)
def get_geo_list():
    df = get_geo_full_list()
    df = filter_relevant_plants(df)
    df = filter_operating_plants(df)
    df = set_lignite_plants(df)
    df = set_gasCC_plants(df)

    df["fuel"] = df["fuel"].str.lower()

    reverse_ana = {v: k for k, v in mp.COUNTRIES_FOR_ANALYSIS.items()}
    df.insert(loc=3, column="cy", value=df["country"].map(reverse_ana))

    return df[df.capa.notnull()]


def set_gasCC_plants(df: pd.DataFrame) -> pd.DataFrame:
    is_gas = df["fuel"] == "Gas"

    df["cc_weight"] = np.nan
    df.loc[is_gas, "cc_weight"] = df.loc[is_gas, "plant_type"].map(CC_WEIGHTING)
    # is_cc = df["cc_weight"][is_gas].apply(round).astype("bool")
    is_cc = df["cc_weight"] >= .5
    df.loc[is_gas & is_cc, "fuel"] = "Gas_cc"
    return df


def set_lignite_plants(df: pd.DataFrame) -> pd.DataFrame:
    is_coal = df["fuel"] == "Coal"
    is_lignite = df["primary_fuel"].str.contains("lignite", case=False)
    is_peat = df["primary_fuel"].str.contains("peat", case=False)
    df.loc[is_coal & (is_lignite ^ is_peat), "fuel"] = "Lignite"
    return df


def filter_operating_plants(df: pd.DataFrame) -> pd.DataFrame:
    no_status = df.status.isna()
    contains_shutdown = df.name.str.contains("(Shutdown)")
    df.loc[no_status & contains_shutdown, "status"] = "Shutdown"
    is_operating = ~df["status"].isin(NON_OPERATIONAL_STATUSES)
    return df[is_operating]


def filter_relevant_plants(df: pd.DataFrame) -> pd.DataFrame:
    is_ana = df["Country"].isin(mp.COUNTRIES_FOR_ANALYSIS.values())
    is_conv = df["Type"].isin(["Gas", "Coal", "Nuclear", "Oil"])
    return df.loc[is_ana & is_conv, COLS.keys()].rename(columns=COLS)


def get_geo_full_list(cache: bool = True) -> pd.DataFrame:

    fp_h5 = paths.CACHE_DIR / DB_FILE_FORMAT.format(filetype="h5")

    if cache and fp_h5.exists():
        df = pd.read_hdf(fp_h5)

    else:
        fp_db = DB_DIR / DB_FILE_FORMAT.format(filetype="db")

        if not fp_db.exists():
            download_database()

        conn = sqlite3.connect(fp_db)
        df = pd.read_sql_query("SELECT * FROM powerplants", conn)
        conn.close()
        if cache:
            hp.write_array(df, fp_h5)

    return df


def download_database() -> None:
    url_base = "https://morph.io/coroa/global_energy_observatory_power_plants/"
    morph_api_key = get_morph_api_key()
    url_ending = f"data.sqlite?key={morph_api_key}"
    url = url_base + url_ending

    date_time = datetime.now().strftime("%Y-%m-%d")
    fp = DB_DIR / DB_FILE_FORMAT.format(filetype="db")

    response = requests.get(url)

    print(f"{fp.name} downloaded from GEO via Morph.")

    with open(fp, 'wb') as file:
        file.write(response.content)


def get_morph_api_key(fp: str = None):
    """Get Morph API-key."""

    fp = paths.KEYS_DIR / "morph.txt" if fp is None else Path(fp)

    try:
        return fp.read_text().strip()

    except FileNotFoundError as e:
        print("morph.txt file not found", e)
