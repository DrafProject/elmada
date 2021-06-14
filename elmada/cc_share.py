"""Web-scrapers for the CCGT-share of the gas-fired power plants"""
import collections
import logging
from functools import lru_cache
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple, Union

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

from elmada import eu_pwl, from_geo_via_morph
from elmada import helper as hp
from elmada import mappings as mp
from elmada import paths

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARN)


# @lru_cache(maxsize=1)
# def get_pp_sizes(replace_nans_by_mean: bool = True, short_countries: bool = True):
#     fuels = ["nuclear", "coal", "gas_cc", "gas", "oil"]
#     df = pd.DataFrame({fuel: get_geo_capa_with_cc(fuel) for fuel in fuels})

#     if short_countries:
#         df = transform_countryindex_to_short(df)

#     if replace_nans_by_mean:
#         logger.info(f"Filled nan's with the following mean values:\n{df.mean()}")
#         df = df.fillna(df.mean())
#     df["lignite"] = df["coal"]
#     return df


# def transform_countryindex_to_short(df: Union[pd.Series, pd.DataFrame]):
#     reverse_ana = {v: k for k, v in mp.COUNTRIES_FOR_ANALYSIS.items()}
#     df.index = df.index.map(reverse_ana)
#     return df.sort_index()


# def get_geo_capa_with_cc(fuel: str):
#     if "gas" in fuel:
#         df = get_rich_geo_list(filter="ana")
#         if fuel == "gas_cc":
#             df = df[df["counts_as_cc"]]
#         elif fuel == "gas":
#             df = df[~df["counts_as_cc"]]

#     else:
#         df = get_geo_list(fuel=fuel, filter="ana")

#     return df.groupby("country").capa.mean()


@lru_cache(maxsize=1)
def get_ccgt_shares_from_cascade():
    # geo = get_geo_shares_overview()["share_cc"].rename("geo")
    # rich_geo = get_rich_geo_shares_overview()["share_cc"].rename("rich_geo")
    rich_geo = from_geo_via_morph.get_ccgt_shares()["share_cc"].rename("rich_geo")
    wiki = get_wiki_shares(cache=True).rename("manual")
    opsd = pd.Series({"DE": get_ccgt_DE()}).rename("opsd")

    df = pd.concat([wiki, rich_geo, opsd], 1, sort=False)

    def select_source(row):
        if not np.isnan(row["opsd"]):
            return "opsd"
        elif not np.isnan(row["rich_geo"]):
            return "rich_geo"
        elif not np.isnan(row["manual"]):
            return "manual"

    def get_selected(row):
        source = row["source"]
        return row[source]

    df["source"] = df.apply(select_source, 1)
    df["selected"] = df.apply(get_selected, 1)
    # df.reindex(mp.COUNTRIES_FOR_ANALYSIS.keys())
    df = df.sort_index()
    return df


#################################
# RICH GEO LIST self-scraped    #
#################################


# def get_rich_geo_shares_overview():
#     geo = get_rich_geo_list()
#     valid_countries = get_valid_countries()
#     header = ["cy_long", "nplants", "total_capa"]
#     df = pd.DataFrame(index=valid_countries.keys(), columns=header)

#     for cy_short, cy_long in valid_countries.items():
#         is_country = geo.country == cy_long
#         df.loc[cy_short, "cy_long"] = cy_long
#         df.loc[cy_short, "nplants"] = is_country.sum()
#         df.loc[cy_short, "cc_capa"] = geo.loc[is_country, "capa"] @ geo.loc[is_country, "cc_weight"]
#         df.loc[cy_short, "total_capa"] = geo.loc[is_country, "capa"].sum()

#     df["share_cc"] = df["cc_capa"] / df["total_capa"]
#     return df


# def get_rich_geo_list(
#     country_long: Optional[str] = None, filter: Optional[str] = None, cache: bool = True
# ):
#     fp = paths.CACHE_DIR / f"geo_list_rich.h5"

#     if cache and fp.exists():
#         df = pd.read_hdf(fp)

#     else:
#         df = get_geo_list()
#         in_valid_countries = df["country"].isin(get_valid_countries().values())
#         df["type"] = np.nan
#         df.loc[in_valid_countries, "type"] = df.loc[in_valid_countries, "geoid"].apply(
#             get_geo_plant_type
#         )
#         if cache:
#             hp.write(df, fp)

#     df.type.replace("Please Select", np.nan, inplace=True)

#     cc_weighting = {
#         "Thermal and CCGT": 1,
#         "Power and Heat Combined Cycle Gas Turbine": 1,
#         "Sub-critical Thermal": 0,
#         "Combined Cycle Gas Turbine": 1,
#         "Power and Heat Open Cycle Gas Turbine": 0,
#         "Open Cycle Gas Turbine": 0,
#         "Heat and Power Steam Turbine": 0,
#         "Super-critical Thermal": 0,
#         "Combined Cycle Gas Engine (CCGE)": 1,
#         "Gas Engines": 0,
#         "OCGT and CCGT": 0.49,
#         np.nan: 0,
#     }

#     df["cc_weight"] = df["type"].map(cc_weighting)
#     df["counts_as_cc"] = df["cc_weight"].apply(round).astype("bool")

#     if country_long is None and filter is None:
#         return df
#     elif country_long is not None and filter is None:
#         return df[df["country"] == country_long]
#     elif country_long is None and filter is not None:
#         if filter == "ana":
#             return df[df.country.isin(mp.COUNTRIES_FOR_ANALYSIS.values())]
#         elif filter == "eur":
#             return df[df.country.isin(mp.EUROPE_COUNTRIES.values())]
#         else:
#             RuntimeError("Filter must be either 'ana' or 'eur'.")
#     else:
#         raise RuntimeError("Country_long and filter given but only one of the two expected.")


#################################
# OPSD POWER PLANT LIST         #
#################################


def get_ccgt_DE() -> pd.Series:
    ser = eu_pwl.prep_installed_generation_capacity(
        year=2019, country="DE", source="power_plant_list"
    )
    return ser["gas_cc"] / (ser["gas_cc"] + ser["gas"])


#################################
# GEO LIST self-scraped         #
#################################


def get_geo_shares_overview() -> pd.DataFrame:
    geo = get_geo_list()
    valid_countries = get_valid_countries()
    header = ["cy_long", "nplants", "total_capa"]
    df = pd.DataFrame(index=valid_countries.keys(), columns=header)

    for cy_short, cy_long in valid_countries.items():
        is_country = geo.country == cy_long
        df.loc[cy_short, "cy_long"] = cy_long
        df.loc[cy_short, "nplants"] = is_country.sum()
        df.loc[cy_short, "cc_capa"] = geo.loc[is_country & geo.is_ccgt, "capa"].sum()
        df.loc[cy_short, "total_capa"] = geo.loc[is_country, "capa"].sum()

    df["share_cc"] = df["cc_capa"] / df["total_capa"]
    return df


def get_valid_countries() -> collections.OrderedDict:
    df = get_geo_list()
    avail = set(df["country"].unique())
    d = {short: long for short, long in mp.COUNTRIES_FOR_ANALYSIS.items() if long in avail}
    return collections.OrderedDict(sorted(d.items()))


# def get_geo_plant_type(geoid):
#     if geoid is None:
#         return np.nan
#     else:
#         url = "http://globalenergyobservatory.org/geoid/" + geoid
#         page = requests.get(url).text
#         soup = BeautifulSoup(page, "lxml")
#         selector = soup.find("select", {"id": "Type_of_Plant_enumfield_rng1"})
#         x = selector.find("option", dict(selected="selected"))
#         if x is None:
#             return np.nan
#         else:
#             return x.get_text()


def get_geo_list(
    country_long: Optional[str] = None,
    filter: Optional[str] = None,
    fuel="gas",
    cache: bool = True,
) -> pd.DataFrame:
    """possible conventional fuels are: gas, coal, nuclear, oil"""
    fp = paths.mode_dependent_cache_dir() / f"geo_list_{fuel}.parquet"

    if cache and fp.exists():
        df = hp.read(fp)

    else:
        fuel_ = fuel.capitalize()
        base_url = "http://globalenergyobservatory.org/"
        url = base_url + f"list.php?db=PowerPlants&type={fuel_}"
        page = requests.get(url).text
        soup = BeautifulSoup(page, "lxml")
        my_table = soup.find("table")
        headers = [cell.get_text().strip() for cell in my_table.find_all("h2")]
        ncols = len(headers)
        entries = my_table.findAll("td")

        df = pd.DataFrame(
            {
                "name": [x.get_text() for x in entries[ncols + 0 :: 4]],
                "geoid": [
                    x.find("a").get_attribute_list("href")[0].split("/")[1].strip()
                    for x in entries[ncols + 0 :: 4]
                ],
                "capa": [cell.get_text().strip() for cell in entries[ncols + 1 :: 4]],
                "country": [cell.get_text().strip() for cell in entries[ncols + 2 :: 4]],
                "state": [cell.get_text().strip() for cell in entries[ncols + 3 :: 4]],
            }
        )
        # df.loc[df["country"] == "Czech Republic", "country"] = "Czechia"
        df.loc[df.capa == ""] = np.nan
        df["is_ccgt"] = df.name.str.contains("CCGT").astype(bool)
        df["capa"] = df["capa"].astype(np.float)
        if cache:
            hp.write(df, fp)

    if country_long is None and filter is None:
        return df
    elif country_long is not None and filter is None:
        return df[df["country"] == country_long]
    elif country_long is None and filter is not None:
        if filter == "ana":
            return df[df.country.isin(mp.COUNTRIES_FOR_ANALYSIS.values())]
        elif filter == "eur":
            return df[df.country.isin(mp.EUROPE_COUNTRIES.values())]
        else:
            ValueError("`filter` must be either 'ana' or 'eur'.")
    else:
        raise ValueError("Country_long and filter given but only one of the two expected.")


#################################
# MANUAL                        #
#################################


def get_wiki_shares(cache: bool = True) -> pd.Series:
    fp = paths.mode_dependent_cache_dir() / "share_ccgt_wiki.parquet"
    if cache and fp.exists():
        ser = hp.read(fp)
    else:
        shares = {
            "AT": get_ccgt_AT(),
            "DK": get_ccgt_DK(),
            "IE": get_ccgt_IE(),
            "IT": get_ccgt_IT(),
            "RS": get_ccgt_RS(),
        }
        ser = pd.Series(shares)
        if cache:
            hp.write(ser, fp)
    return ser


def get_ccgt_IE():
    url = "https://en.wikipedia.org/w/index.php?&oldid=942359418"
    page = requests.get(url).text
    soup = BeautifulSoup(page, "lxml")

    my_table = soup.find("table", {"class": "wikitable sortable"})
    headers = [cell.get_text() for cell in my_table.findAll("th")]
    ncols = len(headers)
    rows = my_table.findAll("tr")

    df = pd.DataFrame(columns=headers)
    for i, row in enumerate(rows):
        cells = row.find_all("td")
        if len(cells) == ncols:
            df.loc[i, :] = [cell.get_text() for cell in cells]

    is_gas = df["Primary Fuel"] == "Gas"
    is_cc = df["Cycle"] == "Combined Cycle"
    capa_gasCC = df.loc[is_gas & is_cc, "Capacity (MW)"].astype("int").sum()
    capa_gas = df.loc[is_gas, "Capacity (MW)"].astype("int").sum()
    return capa_gasCC / capa_gas


def get_ccgt_AT():
    url = "https://de.wikipedia.org/w/index.php?oldid=199043393"
    page = requests.get(url).text
    soup = BeautifulSoup(page, "lxml")

    my_table = soup.find_all("table", {"class": "wikitable sortable"})[3]

    headers = [cell.get_text().rstrip("\n") for cell in my_table.findAll("th")]
    ncols = len(headers)
    rows = my_table.findAll("tr")

    df = pd.DataFrame(columns=headers)
    for i, row in enumerate(rows):
        cells = row.find_all("td")
        if len(cells) == ncols:
            df.loc[i, :] = [cell.get_text().rstrip("\n") for cell in cells]

    df = (
        df.replace(r"\[(.*?)\]", "", regex=True)
        .replace(r"\n", "", regex=True)
        .replace(",", ".", regex=True)
    )
    df.columns = [col.replace("\n", "") for col in df.columns]
    cap_col = "Leistung Elektrischin MWel"
    df[cap_col] = df[cap_col].astype("float")

    # manually entered by research on de.wikipedia.org pages on 2020-04-24:
    is_ccgt = {
        "Gas- und Dampfkraftwerk Mellach": True,
        "Kraftwerk Theiß": True,
        "Kraftwerk Simmering \xa01": False,
        "Kraftwerk Simmering \xa03": False,
        "Kraftwerk Simmering \xa02": True,
        "Gas- und Dampfkraftwerk Timelkam": False,  # n/a
        "Dampfkraftwerk Donaustadt \xa03": True,
        "Fernheizkraftwerk Linz-Mitte": True,
        "Linz Süd": False,  # n/a
        "Kraftwerk Korneuburg \xa01": True,
        "Gas- und Dampfkraftwerk Leopoldau": True,
        "Heizkraftwerk Salzburg Mitte": False,
        "Heizkraftwerk Salzburg Nord": False,
        "Müllverbrennungsanlage Spittelau": False,
    }

    df["is_ccgt"] = df.Name.map(is_ccgt)
    return df[df.is_ccgt][cap_col].sum() / df[cap_col].sum()


def get_ccgt_IT():
    url = "https://de.wikipedia.org/w/index.php?&oldid=194656154"
    page = requests.get(url).text
    soup = BeautifulSoup(page, "lxml")

    my_table = soup.find_all("table", {"class": "wikitable sortable"})[1]

    headers = [cell.get_text() for cell in my_table.findAll("th")]
    ncols = len(headers)
    rows = my_table.findAll("tr")

    df = pd.DataFrame(columns=headers)
    for i, row in enumerate(rows):
        cells = row.find_all("td")
        if len(cells) == ncols:
            df.loc[i, :] = [cell.get_text() for cell in cells]

    df = df.replace(r"\[(.*?)\]", "", regex=True).replace(r"\n", "", regex=True)
    df.columns = [col.replace("\n", "") for col in df.columns]

    cap_col = "Inst. Leistung (MW)"
    df[cap_col] = df[cap_col].astype("float")
    df = df[(df.Brennstoff == "Erdgas") | (df.Brennstoff == "Erdgas/Kohle")].reset_index(drop=True)

    # manually entered by research on 2020-04-28:
    geo_url = "http://globalenergyobservatory.org/geoid/"
    is_ccgt = {
        "Alessandro Volta": [1, "https://de.wikipedia.org/w/index.php?oldid=194580946"],
        "Aprilia": [1, geo_url + "43990"],
        "Bertonico-Turano": [1, geo_url + "43994"],
        "Brindisi (A2A) (Brindisi Nord)": [1, geo_url + "43701"],
        "Brindisi (EniPower)": [1, geo_url + "43980"],
        "Cassano d’Adda": [1, geo_url + "2583"],
        "Chivasso": [1, geo_url + "43682"],
        "Ferrara": [1, geo_url + "43699"],
        "Ferrera Erbognone": [1, geo_url + "43700"],
        "Gissi": [1, geo_url + "43708"],
        "La Casella": [1, geo_url + "43771"],
        "La Spezia 'Eugenio Montale'": [1, geo_url + "43724"],
        "Livorno Ferraris": [1, geo_url + "43684"],
        "Ostiglia": [1, geo_url + "43694"],
        "Piacenza": [1, geo_url + "43692"],
        "Ravenna": [1, geo_url + "43702"],
        "Rossano": [0.5, geo_url + "44001"],
        "Scandale": [1, geo_url + "43696"],
        "Sermide": [1, geo_url + "43686"],
        "Simeri Crichi": [1, geo_url + "43979"],
        "Tavazzano": [1, geo_url + "43695"],
        "Torrevaldaliga Süd": [1, geo_url + "43713"],
        "Turbigo": [0.5, geo_url + "43685"],
        "Vado Ligure": [1, geo_url + "42714"],
    }

    df2 = pd.DataFrame.from_dict(is_ccgt, "index", columns=["is_ccgt", "source"]).reset_index(
        drop=True
    )
    df = pd.concat([df, df2], 1)
    df["is_ccgt"] = df["is_ccgt"].astype("float")

    return (df[cap_col] * df["is_ccgt"]).sum() / df[cap_col].sum()


def get_ccgt_DK():
    # manually entered by research on http://globalenergyobservatory.org/ pages on 2020-04-28:
    geo_url = "http://globalenergyobservatory.org/"
    df = pd.DataFrame(
        [
            [
                "HC Orsted CHP Power Plant Denmark",
                185,
                True,
                geo_url + "form.php?pid=44235",
            ],
            [
                "Skaerbaek CHP Power Plant Denmark",
                392,
                False,
                geo_url + "form.php?pid=44237",
            ],
            [
                "Svanemolle CHP Power Plant Denmark",
                81,
                False,
                geo_url + "form.php?pid=44234",
            ],
        ],
        columns=["name", "capa", "is_ccgt", "source"],
    )
    return df.loc[df["is_ccgt"], "capa"].sum() / df["capa"].sum()


def get_ccgt_RS():
    # 2020-04-29 manually entered by research wiki on https://en.wikipedia.org/w/index.php?oldid=944728190
    # : There is only one Gas-power plant in Serbia (Panonske TE-TO) which is not an CCGT.
    return 0.0
