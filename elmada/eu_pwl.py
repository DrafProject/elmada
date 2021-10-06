import logging
from functools import lru_cache
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

import pandas as pd

from elmada import cc_share, from_entsoe, from_geo_scraped, from_opsd, from_other
from elmada import mappings as mp

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.WARN)


def prep_prices(year=2019, freq="60min", country="DE", **kwargs) -> pd.Series:
    return prep_CEFs(year=year, freq=freq, country=country, **kwargs)["marginal_cost"]


def prep_CEFs(
    year: int = 2019,
    freq: str = "60min",
    country: str = "DE",
    validation_mode: bool = False,
    mo_P: Optional[pd.DataFrame] = None,
    **mo_kwargs,
) -> pd.DataFrame:
    """Prepares XEFs for European countries with piece-wise-linear approximation method"""

    if mo_P is None:
        mo_P = merit_order(year=year, country=country, validation_mode=validation_mode, **mo_kwargs)
    return from_opsd.get_CEFs_from_merit_order(mo_P=mo_P, year=year, freq=freq, country=country)


def merit_order(
    year: int = 2019,
    country: str = "DE",
    approx_method: str = "regr",
    validation_mode: bool = False,
    overwrite_carbon_tax: Optional[float] = None,
    pp_size_method: str = "from_geo_scraped",
) -> pd.DataFrame:
    """Return a merit-order list. Virtual power plants are constructed through discretization."""

    mo_f = merit_order_per_fuel(
        year=year, country=country, approx_method=approx_method, validation_mode=validation_mode
    )

    df = discretize_merit_order_per_fuel(mo_f, pp_size_method=pp_size_method, country=country)

    df["x_k"] = df["fuel_draf"].map(from_other.get_fuel_prices(year=year, country=country))

    DATA_QUASCH = from_other.get_emissions_per_fuel_quaschning()
    marginal_emissions_of_gen = df["fuel_draf"].map(DATA_QUASCH) / df["used_eff"]
    df["fuel_cost"] = df["x_k"] / df["used_eff"]

    carbon_price = (
        from_other.get_ETS_price(year) if overwrite_carbon_tax is None else overwrite_carbon_tax
    )
    df["GHG_cost"] = marginal_emissions_of_gen * carbon_price
    df["marginal_emissions"] = marginal_emissions_of_gen
    df["marginal_cost"] = df["fuel_cost"] + df["GHG_cost"]

    df = df.sort_values("marginal_cost").reset_index(drop=True)
    df["cumsum_capa"] = df["capa"].cumsum()
    df = df.dropna()
    return df.copy()


def merit_order_per_fuel(
    year: int = 2019,
    country: str = "DE",
    approx_method: str = "regr",
    validation_mode: bool = False,
) -> pd.DataFrame:
    """Returns a non-discretized merit order on fuel-type level."""
    eff_min, eff_max, __, __ = approximate_min_max_values(method=approx_method)

    source = "power_plant_list" if validation_mode else "entsoe"

    df = pd.DataFrame(
        dict(
            eff_min=eff_min,
            eff_max=eff_max,
            fuel_price=from_other.get_fuel_prices(year=year, country=country),
            emissions_for_gen=from_other.get_emissions_per_fuel_quaschning(),  # in t_CO2eq / MWh_el
            capa=prep_installed_generation_capacity(year=year, country=country, source=source),
        )
    )

    logger.info(f"Available fuels for {year}, {country}: {list(df.index)}")

    df["eff_mean"] = (df["eff_min"] + df["eff_max"]) / 2
    df["fuel_cost"] = df["fuel_price"] / df["eff_mean"]
    df["GHG_cost"] = df["emissions_for_gen"] / df["eff_mean"]
    df["marginal_cost"] = df["fuel_cost"] + df["GHG_cost"]
    df = df.sort_values("marginal_cost")
    df["cumsum_capa"] = df["capa"].cumsum()
    return df.copy()


@lru_cache(maxsize=2)
def approximate_min_max_values(method="regr") -> Tuple[Dict, Dict, Dict, Dict]:
    """`method` must be either 'interp' for interpolation or 'regr' for linear regression."""
    mo = get_clean_merit_order_for_min_max_approximation(sort_by_fuel=True)

    if method == "interp":
        grouper = mo.groupby("fuel_draf")["used_eff"]
        eff_min = grouper.min().to_dict()
        eff_max = grouper.max().to_dict()

        grouper = mo.groupby("fuel_draf")["cumsum_capa"]
        cumsum_capa_LHS = grouper.min().to_dict()
        cumsum_capa_RHS = grouper.max().to_dict()

    elif method == "regr":
        from scipy import stats

        eff_min = {}
        eff_max = {}
        cumsum_capa_LHS = {}
        cumsum_capa_RHS = {}

        for fuel in mo["fuel_draf"].unique():
            mo_ = mo[mo["fuel_draf"] == fuel]
            slope, intercept, r_value, p_value, std_err = stats.linregress(
                mo_["cumsum_capa"], mo_["used_eff"]
            )

            cumsum_capa_LHS[fuel] = mo_["cumsum_capa"].min()
            cumsum_capa_RHS[fuel] = mo_["cumsum_capa"].max()

            eff_min[fuel] = intercept + slope * cumsum_capa_RHS[fuel]
            eff_max[fuel] = intercept + slope * cumsum_capa_LHS[fuel]

    else:
        raise ValueError(f"Method must be either 'interp' or 'regr'. Given:'{method}'")

    return eff_min, eff_max, cumsum_capa_RHS, cumsum_capa_LHS


def get_clean_merit_order_for_min_max_approximation(sort_by_fuel=False) -> pd.DataFrame:
    """Return a clean German merit order of the generation technologies."""

    # The opsd-file is used here here!
    mo = from_opsd.merit_order(year=2019)

    if sort_by_fuel:
        groups = []
        for fuel, group in mo.groupby("fuel_draf", sort=False):
            groups.append(group.sort_values(by="used_eff", ascending=False))

        mo = pd.concat(groups, axis=0, ignore_index=True)

        mo["cumsum_capa"] = mo["capa"].cumsum()

    return mo


@lru_cache(maxsize=3)
def prep_installed_generation_capacity(year=2019, country="DE", source="entsoe") -> pd.Series:

    if source == "power_plant_list":
        ser = (
            from_opsd.merit_order(year=year)[["fuel_draf", "capa"]]
            .groupby("fuel_draf")
            .sum()["capa"]
        )
        return ser

    elif source == "entsoe":
        df = from_entsoe.load_installed_generation_capacity(year=year, country=country)
        df = from_entsoe.aggregate_to_standard_techs(df)
        ser = df.T.iloc[:, 0]

        ser = apply_share_cc_assumption(ser, country=country)

        logger.info(f"Available fuels for {year}, {country}: {list(ser.index)}")

        ser = pd.Series(index=mp.PWL_FUELS, data=ser)
        ser.fillna(0, inplace=True)
        return ser

    # elif source == "opsd":
    #     ser = from_opsd.get_installed_generation_capacity(year=year, country=country)
    #     ser = pd.Series(index=mp.PWL_FUELS, data=ser)
    #     ser.fillna(0, inplace=True)
    #     ser = apply_share_cc_assumption(ser, country=country)
    #     return ser

    else:
        raise ValueError("Source must be either 'entsoe' or 'power_plant_list'")


def apply_share_cc_assumption(ser, country: str) -> pd.Series:
    if "gas" in ser:
        share_cc = get_share_cc(country=country)
        ser["gas_cc"] = ser["gas"] * share_cc
        ser["gas"] = ser["gas"] * (1 - share_cc)

    return ser


def get_share_cc(country: str) -> float:
    try:
        return cc_share.get_ccgt_shares_from_cascade().loc[country, "selected"]
    except KeyError:
        logger.warning("Unable to apply cascade method, German values returned")
        return cc_share.get_ccgt_DE()


def discretize_merit_order_per_fuel(
    mo_f: pd.DataFrame, country: str, pp_size_method: str = "from_geo_scraped"
) -> pd.DataFrame:

    concat_list = []
    # if country=="DE":
    #     pp_size_method = "from_Germany"
    for fuel, row in mo_f.iterrows():
        pp_size = get_pp_size(pp_size_method=pp_size_method, country=country, fuel=fuel)
        logger.info(f"pp_size_method={pp_size_method}")
        number_of_powerplants = int(row["capa"] // pp_size)
        capa_of_last_powerplant = row["capa"] % pp_size
        df = pd.DataFrame({"capa": [pp_size] * number_of_powerplants + [capa_of_last_powerplant]})
        cumsum_capa_in_f = df["capa"].cumsum()
        df["used_eff"] = row["eff_max"] - (cumsum_capa_in_f / row["capa"]) * (
            row["eff_max"] - row["eff_min"]
        )
        df["fuel_draf"] = fuel
        concat_list.append(df)
    df = pd.concat(concat_list, ignore_index=True)
    return df


def get_pp_size(pp_size_method: str, country: str, fuel: str) -> int:
    try:
        if pp_size_method == "from_geo_scraped":
            return from_geo_scraped.get_pp_sizes_for_pwl().loc[country, fuel]
        # elif pp_size_method == "from_Germany":
        #     return get_pp_sizes_from_germany()[fuel]
        # elif pp_size_method == "from_geo":
        #     return from_geo_via_morph.get_pp_sizes().loc[country, fuel]
        # elif pp_size_method == "from_ccgt":
        #     return cc_share.get_pp_sizes().loc[country, fuel]
        else:
            raise ValueError(f"Invalid pp_size_method given: {pp_size_method}")
    except KeyError:
        logger.warning("Unable to apply pp-size, German values returned")
        return get_pp_sizes_from_germany()[fuel]


@lru_cache(maxsize=1)
def get_pp_sizes_from_germany() -> pd.Series:
    return from_opsd.merit_order().groupby("fuel_draf").capa.mean()
