"""Reads power plant list from Open Power System Data (OPSD)."""

import logging
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from scipy import stats

from elmada import el_entsoepy as ep
from elmada import el_other as ot
from elmada import mappings as mp
from elmada import paths
import elmada

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARN)


def plot_merit_order_plt(year=2019, variant=1, **kwargs) -> None:
    plt.rcParams.update({"mathtext.default": "regular"})
    fig, ax_left = plt.subplots(figsize=(7, 4))
    ax_right = ax_left.twinx()

    if variant == 1:
        # TODO: Probem: Tilted area under line.
        df = prepare_merit_order_for_plt(
            year, which="marginal_cost", split_across_columns=True, **kwargs
        )
        colors = ep.get_colors(df)
        df.plot(kind="area", ax=ax_left, linewidth=0, color=colors)

    elif variant == 2:
        # TODO: Area must be colored according to fuel. Legend
        df = prepare_merit_order_for_plt(
            year, which="marginal_cost", split_across_columns=False, **kwargs
        )
        df["marginal_cost"].plot(kind="area", ax=ax_left)

    elif variant == 3:
        # TODO: Problem: Gaps between the colored sections
        df = prepare_merit_order_for_plt(
            year, which="marginal_cost", split_across_columns=True, **kwargs
        )
        for f in df:
            plt.fill_between(x=df.index, y1=df[f], step="post", interpolate=True, ax=ax_left)

    plt.tight_layout()
    ax_left.set_ylabel(r"Marginal cost $c_p^m$ [€ / $MWh_{el}$]")
    ax_left.set_xlabel(r"Net power [GW]")

    df = prepare_merit_order_for_plt(year, which="marginal_emissions", **kwargs)
    df.plot(ax=ax_right, color="black", legend=None, linewidth=2)
    df["nuclear"].plot(
        ax=ax_right,
        legend=True,
        color="black",
        linewidth=2,
        label=r"Marg. emissions $\varepsilon_p$",
    )  # just to get legend
    ax_right.set_ylabel(r"Marginal emissions $\varepsilon_p$ [$t_{CO_{2}eq}$ / $MWh_{el}$]")
    ax_right.set_ylim(bottom=0, top=None)


def plot_merit_order_plotly(year=2019, mo_P=None, **kwargs) -> "PlotlyPlot":
    import plotly.express as px

    if mo_P is None:
        mo_P = merit_order(year, **kwargs)
    return px.area(
        mo_P,
        x="cumsum_capa",
        y="marginal_cost",
        color="fuel_draf",
        color_discrete_map=mp.TECH_COLORS,
    )


def plot_marginal_emissions_plotly(year=2019, mo_P=None, **kwargs) -> "PlotlyPlot":
    import plotly.express as px

    df = prep_CEFs(year=year, mo_P=mo_P, **kwargs)
    return px.scatter(df, y="MEFs", color="marginal_fuel", color_discrete_map=mp.TECH_COLORS)


def plot_marginal_emissions_plt(year=2019, mo_P=None, **kwargs) -> None:
    df = prep_CEFs(year=2019, mo_P=mo_P, **kwargs)
    fuels = df["marginal_fuel"].unique().tolist()
    colors = ep.get_colors(fuels)
    _, ax = plt.subplots(1, figsize=(8, 6))
    ax.set_ylabel("Marginal emissions [$t_{CO_{2}eq}$ / $MWh_{el}$]")

    for f, c in zip(fuels, colors):
        df.marginal_emissions.where(df["marginal_fuel"] == f).plot(ax=ax, color=c)


def prepare_merit_order_for_plt(
    year: int, which: str, split_across_columns=True, **kwargs
) -> pd.DataFrame:
    df = merit_order(year, **kwargs)
    df = df[["fuel_draf", "cumsum_capa", which]]
    df["cumsum_capa"] /= 1000  # convert from kWh to MWh
    df = df.set_index("cumsum_capa", drop=True)
    fuels = list(df["fuel_draf"].unique())
    if split_across_columns:
        for f in fuels:
            df[f] = df.where(df["fuel_draf"] == f)[which]
        return df[fuels]
    else:
        return df


def prep_prices(year=2019, freq="60min", country="DE", **mo_kwargs) -> pd.Series:
    """Convenience function to get the marginal costs for each timesteps."""
    return prep_CEFs(year=year, freq=freq, country=country, **mo_kwargs)["marginal_cost"]


def prep_CEFs(year=2019, freq="60min", country="DE", mo_P=None, **mo_kwargs) -> pd.DataFrame:
    """Prepares German CEFs from the power plant list from OPSD"""
    assert country == "DE", "this function only works for Germany"
    if mo_P is None:
        mo_P = merit_order(year=year, **mo_kwargs)
    return get_CEFs_from_merit_order(mo_P=mo_P, year=year, freq=freq, country=country)


def get_CEFs_from_merit_order(
    mo_P: pd.DataFrame, year: int, freq: str, country: str, resi_T: Optional[pd.Series] = None
) -> pd.DataFrame:
    if resi_T is None:
        resi_T = ep.prep_residual_load(year=year, freq=freq, country=country)
    _warn_if_not_enough_capa(mo_P, resi_T)
    total_load_T = ep.load_el_national_generation(year=year, freq=freq, country=country).sum(axis=1)
    cols = ["cumsum_capa", "marginal_emissions", "capa", "fuel_draf", "used_eff", "marginal_cost"]
    len_mo = len(mo_P)
    mo_P_arr = mo_P[cols].values
    transm_eff = ot.get_transmission_efficiency(country=country)

    def get_data(resi_value: float, what: str = "marginal_emissions"):
        output_col_index = cols.index(what)
        for row in range(len_mo):
            if mo_P_arr[row, 0] > resi_value:
                return mo_P_arr[row, output_col_index]
        return mo_P_arr[-1, output_col_index]

    def get_emissions_for_xef(resi_value: float):
        # if the residual load is not positive there are no no emissions:
        if resi_value <= 0.0:
            return 0.0

        emissions = 0
        for row in range(len_mo):
            emissions += mo_P_arr[row, 1] * mo_P_arr[row, 2]

            # if the cumsum_capa is above resi_value subtract the emissions of the additional
            # capacity and return the quotient of emissions and resi_value:
            if mo_P_arr[row, 0] > resi_value:
                emissions -= mo_P_arr[row, 1] * (mo_P_arr[row, 0] - resi_value)
                return emissions

        # if the following code is executed there is not enough generation capacity:
        return emissions

    df = pd.DataFrame(
        {
            "residual_load": resi_T,
            "total_load": total_load_T,
            "marginal_fuel": resi_T.apply(get_data, what="fuel_draf"),
            "efficiency": resi_T.apply(get_data, what="used_eff"),
            "marginal_cost": resi_T.apply(get_data, what="marginal_cost"),
            "MEFs": resi_T.apply(get_data, what="marginal_emissions") / transm_eff,
            "XEFs": (resi_T.apply(get_emissions_for_xef)) / total_load_T / transm_eff,
        }
    )

    df["XEFs"] *= 1000  # convert from t/MWh to g/kWh
    df["MEFs"] *= 1000  # convert from t/MWh to g/kWh
    return df


def merit_order(
    year=2019,
    efficiency_per_plant: bool = True,
    emission_data_source: str = "quaschning",
    overwrite_carbon_tax: Optional[float] = None,
    **preprocess_kwargs,
) -> pd.DataFrame:
    """Prepares the merit order from the German power plant list."""

    df = get_current_active_power_plants(year)
    df = _rename_to_draf_fuels(df)
    df = _preprocess_efficiencies(
        df, efficiency_per_plant=efficiency_per_plant, **preprocess_kwargs
    )
    df = _add_marginal_emissions_for_gen(df, emission_data_source)

    carbon_price = ot.get_ETS_price(year) if overwrite_carbon_tax is None else overwrite_carbon_tax
    df["x_k"] = df["fuel_draf"].map(ot.get_fuel_prices(year=year, country="DE"))
    df["fuel_cost"] = df["x_k"] / df["used_eff"]
    df["GHG_cost"] = df["marginal_emissions_for_gen"] * carbon_price
    df["marginal_emissions"] = df["marginal_emissions_for_gen"]
    df["marginal_cost"] = df["fuel_cost"] + df["GHG_cost"]

    # to be consistent with the PWL merit_order:
    df = df.rename(columns={"capacity_net_bnetza": "capa"})

    df = df.sort_values("marginal_cost").reset_index(drop=True)
    df["cumsum_capa"] = df["capa"].cumsum()
    return df


def get_installed_generation_capacity(year=2019, country="DE") -> pd.Series:
    """[NOT USED] This function is only kept for documentation.

    Returns a Series with aggregated installed generation capacity fuel type dependent on year
    and country.

    WARNING:
        - Poor data for year 2016-2017!
        - Better use el_entsoepy.load_installed_generation_capacity
        - This function is just for the purpose of a later evaluation.
        - Several data sources are combined here, the sources are chosen arbitrary with 'last()'.

    Source:
        (https://doi.org/10.25832/national_generation_capacity/2019-12-02)
    """
    fp = (
        paths.DATA_DIR
        / "opsd/opsd-national_generation_capacity-2019-12-02/national_generation_capacity_stacked.csv"
    )
    df = pd.read_csv(fp, index_col=0)
    is_country = df["country"] == country
    is_year = df["year"] == year
    in_technology = df.technology.isin(mp.OPSD_TO_DRAF.keys())
    ser = df.loc[is_country & is_year & in_technology, ["technology", "capacity"]]
    ser = ser.groupby("technology").last().capacity
    ser.index = ser.index.map(mp.OPSD_TO_DRAF)
    ser.index.name = "fuel_draf"
    return ser


def get_summary(year=2019) -> pd.DataFrame:
    ca = get_current_active_power_plants(year)
    grouper = ca.groupby(["fuel", "technology"])
    d = dict(
        counts=grouper.count().id,
        efficiency=grouper.mean()["efficiency_estimate"],
        sum_capa=grouper.sum()["capacity_net_bnetza"],
    )
    return pd.concat(d.values(), axis=1, keys=d.keys())


def get_summary_EU(year=2019) -> pd.DataFrame:
    """[NOT USED]"""
    ca = get_current_active_power_plants_EU(year)
    grouper = ca.groupby(["country", "energy_source", "energy_source_level_2", "technology"])
    d = dict(counts=grouper.count()["name"], sum_capa=grouper.sum()["capacity"])
    return pd.concat(d.values(), axis=1, keys=d.keys())


def get_summary_of_opsd_raw() -> pd.DataFrame:
    df = read_opsd_powerplant_list(which="DE")
    df = df.rename(columns={"capacity_net_bnetza": "capa"})
    df = df.groupby("energy_source_level_2").agg({"id": "size", "capa": "sum"})
    df = df.sort_values("capa", ascending=False)
    df["capa_rel"] = df["capa"] / df["capa"].sum()
    return df


def get_current_active_power_plants(year=2019) -> pd.DataFrame:
    """Returns a Dataframe with all active power plants for a specific year."""
    df = read_opsd_powerplant_list(which="DE")

    used_fuels = mp.OPSD_TO_DRAF.keys()
    other_fuels = set(df["fuel"]) - set(used_fuels)
    is_german = df["country_code"] == "DE"
    after_commissioned = (df["commissioned"].notnull() & (df["commissioned"] < year)) | df[
        "commissioned"
    ].isna()
    before_shutdown = (df["shutdown"].notnull() & (df["shutdown"] > year)) | df["shutdown"].isna()
    currently_active = after_commissioned & before_shutdown
    in_used_fuels = df["fuel"].isin(used_fuels)
    cond = is_german & currently_active & in_used_fuels
    ca = df[cond]

    logger.info(
        f"{(cond.sum() / len(df)):.2%} of data rows were used "
        f"({(~in_used_fuels).sum() / len(df):.2%} are not in used fuels). "
        f"Other (discarded) fuels are {other_fuels}."
    )

    # interesting_cols = ["id", "name_bnetza", "status", "fuel", "technology", "type", "efficiency_estimate", "capacity_net_bnetza"]
    return ca


def get_current_active_power_plants_EU(year=2019) -> pd.DataFrame:
    """[NOT USED] Get current active OPSD power plants for European Union.

    NOTE: The data basis used in this function is not sufficient. In most countries there
    are only one fuel type.
    """
    df = read_opsd_powerplant_list(which="EU")
    used_fuels = mp.OPSD_TO_DRAF.keys()
    other_fuels = df["energy_source_level_2"].unique().tolist()
    after_commissioned = (df["commissioned"].notnull() & (df["commissioned"] < year)) | df[
        "commissioned"
    ].isna()
    has_capa_value = df["capacity"].notnull()
    currently_active = after_commissioned
    in_used_fuels = df["energy_source_level_2"].isin(used_fuels)
    cond = currently_active & has_capa_value & in_used_fuels
    ca = df[cond]

    logger.info(
        f"{(cond.sum() / len(df)):.2%} of data rows were used "
        f"({(~in_used_fuels).sum() / len(df):.2%} are not in used fuels). "
        f"Other (discarded) fuels are {other_fuels}."
    )

    # interesting_cols = ["country", "name", "energy_source_level_2", "technology", "type", "capacity"]
    return ca


def read_opsd_powerplant_list(which: str = "DE") -> pd.DataFrame:
    assert which in ("DE", "EU"), f"`{which}` is no valid value for `which`."
    mode = elmada.get_mode()
    fps = {
        "live": f"OPSD_conventional_power_plants_{which}.csv",
        "safe": f"OPSD_conventional_power_plants_{which}[safe].csv",
    }

    fp = paths.CACHE_DIR / fps[mode]

    if not fp.exists():
        download_powerplant_list(which=which, fp=fp)
    df = pd.read_csv(fp)

    if mode == "live":
        df = df.rename(columns={"energy_source": "fuel", "country": "country_code"})

    return df


def download_powerplant_list(which: str, fp: Path):
    url = (
        f"https://data.open-power-system-data.org/conventional_power_plants/latest/"
        f"conventional_power_plants_{which}.csv"
    )
    response = requests.get(url, allow_redirects=True)

    with open(fp, "wb") as file:
        file.write(response.content)

    print(f"{fp.name} downloaded from OPSD.")


def _rename_to_draf_fuels(
    df: pd.DataFrame, minimum_efficiency_for_gas_cc: float = 0.5
) -> pd.DataFrame:
    def my_rename(row):
        if (
            (row["fuel"] == "Natural gas")
            and (row["technology"] == "Combined cycle")
            and (row["efficiency_estimate"] >= minimum_efficiency_for_gas_cc)
        ):
            return "gas_cc"
        else:
            return mp.OPSD_TO_DRAF[row["fuel"]]

    df["fuel_draf"] = df.apply(my_rename, axis=1)
    return df


def _preprocess_efficiencies(
    df: pd.DataFrame,
    efficiency_per_plant: bool = True,
    fill_missing_efficiencies: bool = True,
    fill_zscore_outlier: bool = True,
    zscore_threshold: float = 3,
    ensure_minimum_efficiency: bool = True,
    minimum_efficiency: float = 0.3,
) -> pd.DataFrame:

    filler_dic = df.groupby(by="fuel_draf").mean()["efficiency_estimate"].to_dict()
    df["filler"] = df["fuel_draf"].map(filler_dic)

    if fill_missing_efficiencies:
        number_of_nans = df["efficiency_estimate"].isna().sum()
        logger.info(f"{number_of_nans} nans in efficiencies of merit order filled")
        df["efficiency_estimate"].fillna(df["filler"], inplace=True)

    if fill_zscore_outlier:
        for fuel in df["fuel_draf"].unique():
            ser = df["efficiency_estimate"]
            ser = ser[ser.notnull()]
            cond_zscore = np.abs(stats.zscore(ser)) > zscore_threshold
            cond_fuel = df["fuel_draf"] == fuel
            number_of_nans = len(df[cond_zscore & cond_fuel])
            logger.info("f{number_of_nans} nans filled in fuel {fuel}.")
            df.loc[(cond_zscore & cond_fuel), "efficiency_estimate"] = filler_dic[fuel]

    df["eta_k"] = df["fuel_draf"].map(ot.get_baumgaertner_data()["eta_k"])
    df["used_eff"] = df["efficiency_estimate"] if efficiency_per_plant else df["eta_k"]

    if ensure_minimum_efficiency:
        df.loc[df["used_eff"] < minimum_efficiency, "used_eff"] = minimum_efficiency
        logger.info(f"Minimum_efficiency set to {minimum_efficiency}.")

    return df


def _add_marginal_emissions_for_gen(df: pd.DataFrame, emission_data_source: str) -> pd.DataFrame:

    if emission_data_source == "baumgaertner":
        DATA_BAUMG = ot.get_baumgaertner_data()
        df["mu_co2_k"] = df["fuel_draf"].map(DATA_BAUMG["mu_co2_k"])
        df["H_u_k"] = df["fuel_draf"].map(DATA_BAUMG["H_u_k"])
        df["marginal_emissions_for_gen"] = df["mu_co2_k"] / (df["H_u_k"] * df["used_eff"])

    elif emission_data_source == "quaschning":
        # in the quaschning data the mu_co2_k and the H_u_k are already included
        DATA_QUASCH = ot.get_emissions_per_fuel_quaschning()
        df["marginal_emissions_for_gen"] = df["fuel_draf"].map(DATA_QUASCH) / df["used_eff"]

    else:
        raise RuntimeError("emission_data_source must be either `baumgaertner or quaschning.")

    return df


def _warn_if_not_enough_capa(mo_P: pd.DataFrame, resi_ser: pd.DataFrame) -> None:
    mo_max = mo_P["cumsum_capa"].max() / 1e3
    min_resi = resi_ser.min() / 1e3
    if mo_max < min_resi:
        logger.warning(
            f"Generation capacity ({mo_max:.2f} GW) is lower than "
            f"minimum residual load ({min_resi:.2f} GW)."
        )
