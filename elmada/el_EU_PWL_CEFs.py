import logging
from functools import lru_cache
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import pandas as pd

from elmada import el_entsoepy as ep
from elmada import el_geo_morph as gm
from elmada import el_opsd as od
from elmada import el_other as ot
from elmada import el_share_CCGT as ccgt
from elmada import geo_scraper as gs
from elmada import mappings as mp

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)


def plot_merit_order_plotly(year=2019, country="DE", mo_P=None, **kwargs):
    import plotly.express as px
    if mo_P is None:
        mo_P = merit_order(year=year, country=country, **kwargs)
    return px.area(
        mo_P,
        x="cumsum_capa",
        y="marginal_cost",
        color="fuel_draf",
        color_discrete_map=mp.TECH_COLORS,
    )


def plot_merit_order_plt(year=2019, country="DE", variant=1, **kwargs):
    plt.rcParams.update({"mathtext.default": "regular"})
    fig, ax_left = plt.subplots(figsize=(7, 4))
    ax_right = ax_left.twinx()

    if variant == 1:
        # TODO: Probem: Tilted area under line.
        df = prepare_merit_order_for_plot(year,
                                          country,
                                          which="marginal_cost",
                                          split_across_columns=True,
                                          **kwargs)
        colors = ep.get_colors(df)
        df.plot(kind="area", ax=ax_left, linewidth=0, color=colors)

    elif variant == 2:
        # TODO: Area must be colored according to fuel. Legend
        df = prepare_merit_order_for_plot(year,
                                          country,
                                          which="marginal_cost",
                                          split_across_columns=False,
                                          **kwargs)
        df["marginal_cost"].plot(kind="area", ax=ax_left)

    elif variant == 3:
        # TODO: Problem: Gaps between the colored sections
        df = prepare_merit_order_for_plot(year,
                                          country,
                                          which="marginal_cost",
                                          split_across_columns=True,
                                          **kwargs)
        for f in df:
            plt.fill_between(x=df.index, y1=df[f], step="post", interpolate=True, ax=ax_left)

    plt.tight_layout()
    ax_left.set_ylabel(r"Marginal cost $c_p^m$ [€ / $MWh_{el}$]")
    ax_left.set_xlabel(r"Net power [GW]")
    ax_left.set_ylim(0, 165)

    df = prepare_merit_order_for_plot(year,
                                      country,
                                      which="marginal_emissions",
                                      split_across_columns=False,
                                      **kwargs)["marginal_emissions"]
    df.plot(drawstyle="steps-post",
            ax=ax_right,
            color="black",
            legend=True,
            linewidth=2,
            label=r"Marg. emissions $\varepsilon_p$")
    ax_right.set_ylim(0, 1.8)
    ax_right.set_ylabel(r"Marginal emissions $\varepsilon_p$ [$t_{CO_{2}eq}$ / $MWh_{el}$]")
    ax_right.set_ylim(bottom=0, top=None)


def prepare_merit_order_for_plot(year: int,
                                 country: str,
                                 which: str,
                                 split_across_columns=True,
                                 **kwargs) -> pd.DataFrame:
    df = merit_order(year=year, country=country, **kwargs)
    df = df[["fuel_draf", "cumsum_capa", which]]
    df["cumsum_capa"] /= 1000  # convert from MW to GW
    df.set_index("cumsum_capa", inplace=True, drop=True)
    fuels = list(df["fuel_draf"].unique())
    if split_across_columns:
        for f in fuels:
            df[f] = df.where(df["fuel_draf"] == f)[which]
        return df[fuels]
    else:
        return df


def prep_prices(year=2019, freq="60min", country="DE", **kwargs) -> pd.Series:
    return prep_CEFs(year=year, freq=freq, country=country, **kwargs)["marginal_cost"]


def prep_CEFs(year: int = 2019,
              freq: str = "60min",
              country: str = "DE",
              validation_mode: bool = False,
              mo_P: Optional[pd.DataFrame] = None,
              **mo_kwargs) -> pd.DataFrame:
    """Prepares XEFs for European countries with piece-wise-linear approximation method"""

    if mo_P is None:
        mo_P = merit_order(year=year,
                           country=country,
                           validation_mode=validation_mode,
                           **mo_kwargs)
    return od.get_CEFs_from_merit_order(mo_P=mo_P, year=year, freq=freq, country=country)


def merit_order(year: int = 2019,
                country: str = "DE",
                approx_method: str = "regr",
                validation_mode: bool = False,
                overwrite_carbon_tax: Optional[float] = None,
                pp_size_method: str = "geo_scraper") -> pd.DataFrame:
    """Return a merit-order list. Virtual power plants are constructed through discretization."""

    mo_f = merit_order_per_fuel(year=year,
                                country=country,
                                approx_method=approx_method,
                                validation_mode=validation_mode)

    df = discretize_merit_order_per_fuel(mo_f,
                                         pp_size_method=pp_size_method,
                                         country=country)

    df["x_k"] = df["fuel_draf"].map(ot.get_fuel_prices(year=year, country=country))

    DATA_QUASCH = ot.get_emissions_per_fuel_quaschning()
    marginal_emissions_of_gen = df["fuel_draf"].map(DATA_QUASCH) / df["used_eff"]
    df["fuel_cost"] = df["x_k"] / df["used_eff"]

    carbon_price = ot.get_ETS_price(year) if overwrite_carbon_tax is None else overwrite_carbon_tax
    df["GHG_cost"] = marginal_emissions_of_gen * carbon_price
    df["marginal_emissions"] = marginal_emissions_of_gen
    df["marginal_cost"] = df["fuel_cost"] + df["GHG_cost"]

    df.sort_values("marginal_cost", inplace=True)
    df.reset_index(drop=True, inplace=True)
    df["cumsum_capa"] = df["capa"].cumsum()
    df.dropna(inplace=True)
    return df.copy()


def merit_order_per_fuel(year: int = 2019,
                         country: str = "DE",
                         approx_method: str = "regr",
                         validation_mode: bool = False) -> pd.DataFrame:
    """Returns a non-discretized merit order on fuel-type level."""
    eff_min, eff_max, __, __ = approximate_min_max_values(method=approx_method)

    source = "power_plant_list" if validation_mode else "entsoe"

    df = pd.DataFrame(
        dict(
            eff_min=eff_min,
            eff_max=eff_max,
            fuel_price=ot.get_fuel_prices(year=year, country=country),
            emissions_for_gen=ot.get_emissions_per_fuel_quaschning(),  # in t_CO2eq / MWh_el
            capa=prep_installed_generation_capacity(year=year, country=country, source=source)))

    logger.info(f"Available fuels for {year}, {country}: {list(df.index)}")

    df["eff_mean"] = (df["eff_min"] + df["eff_max"]) / 2
    df["fuel_cost"] = df["fuel_price"] / df["eff_mean"]
    df["GHG_cost"] = df["emissions_for_gen"] / df["eff_mean"]
    df["marginal_cost"] = df["fuel_cost"] + df["GHG_cost"]
    df.sort_values("marginal_cost", inplace=True)
    df["cumsum_capa"] = df["capa"].cumsum()
    return df.copy()


@lru_cache(maxsize=2)
def approximate_min_max_values(method="regr") -> Tuple[Dict, Dict]:
    """method = 'interp' or 'regr'"""
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
                mo_["cumsum_capa"], mo_["used_eff"])

            cumsum_capa_LHS[fuel] = mo_["cumsum_capa"].min()
            cumsum_capa_RHS[fuel] = mo_["cumsum_capa"].max()

            eff_min[fuel] = intercept + slope * cumsum_capa_RHS[fuel]
            eff_max[fuel] = intercept + slope * cumsum_capa_LHS[fuel]

    else:
        raise RuntimeError(f"Method must be either 'interp' or 'regr'. Given:'{method}'")

    return eff_min, eff_max, cumsum_capa_RHS, cumsum_capa_LHS


def get_clean_merit_order_for_min_max_approximation(sort_by_fuel=False) -> pd.DataFrame:
    """Return a clean German merit order of the generation technologies."""

    # The opsd-file is used here here!
    mo = od.merit_order(year=2019)

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
        ser = od.merit_order(year=year)[["fuel_draf", "capa"]].groupby("fuel_draf").sum()["capa"]
        return ser

    elif source == "entsoe":
        df = ep.load_installed_generation_capacity(year=year, country=country)
        df = ep.aggregate_to_standard_techs(df)
        ser = df.T.iloc[:, 0]

        ser = apply_share_cc_assumption(ser, country=country)

        logger.info(f"Available fuels for {year}, {country}: {list(ser.index)}")

        ser = pd.Series(index=mp.PWL_FUELS, data=ser)
        ser.fillna(0, inplace=True)
        return ser

    elif source == "opsd":
        ser = od.get_installed_generation_capacity(year=year, country=country)
        ser = pd.Series(index=mp.PWL_FUELS, data=ser)
        ser.fillna(0, inplace=True)
        ser = apply_share_cc_assumption(ser, country=country)
        return ser

    else:
        raise RuntimeError("source must be either entsoe, opsd or power_plant_list")


def apply_share_cc_assumption(ser, country: str) -> pd.Series:
    if "gas" in ser:
        share_cc = get_share_cc(country=country)
        ser["gas_cc"] = ser["gas"] * share_cc
        ser["gas"] = ser["gas"] * (1 - share_cc)

    return ser


def get_share_cc(country: str, share_cc_method: str = "cascade") -> float:
    try:
        if share_cc_method == "cascade":
            return ccgt.get_ccgt_shares().loc[country, "selected"]
        else:
            raise RuntimeError(f"invalid share_cc_method given: {share_cc_method}")
    except KeyError:
        logger.warning("unable to apply share_cc_method, German values returned")
        return ccgt.get_ccgt_DE()


def discretize_merit_order_per_fuel(mo_f: pd.DataFrame,
                                    country: str,
                                    pp_size_method: str = "geo_scraper") -> pd.DataFrame:

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
        df["used_eff"] = row["eff_max"] - (cumsum_capa_in_f / row["capa"]) * (row["eff_max"] -
                                                                              row["eff_min"])
        df["fuel_draf"] = fuel
        concat_list.append(df)
    df = pd.concat(concat_list, ignore_index=True)
    return df


def get_pp_size(pp_size_method: str, country: str, fuel: str) -> int:
    try:
        if pp_size_method == "from_Germany":
            return get_pp_sizes_from_germany()[fuel]
        elif pp_size_method == "from_geo":
            return gm.get_pp_sizes().loc[country, fuel]
        elif pp_size_method == "from_ccgt":
            return ccgt.get_pp_sizes().loc[country, fuel]
        elif pp_size_method == "geo_scraper":
            return gs.get_pp_sizes_for_pwl().loc[country, fuel]
        else:
            raise RuntimeError(f"invalid pp_size_method given: {pp_size_method}")
    except KeyError:
        logger.warning("unable to apply pp-size, German values returned")
        return get_pp_sizes_from_germany()[fuel]


@lru_cache(maxsize=1)
def get_pp_sizes_from_germany() -> pd.Series:
    return od.merit_order().groupby("fuel_draf").capa.mean()
