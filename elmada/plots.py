from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

from elmada import helper as hp
from elmada import mappings as mp
from elmada.main import get_emissions, get_merit_order, get_residual_load


def merit_order(
    year=2019,
    country="DE",
    method="PWL",
    ylim_left: Optional[float] = None,
    ylim_right: Optional[float] = None,
    ax: Optional["plt.axes"] = None,
    mo_P: Optional[pd.DataFrame] = None,
    include_histo: bool = False,
    include_legend: bool = True,
    legend_fontsize: float = 9,
    **mo_kwargs,
) -> Tuple[plt.Figure, plt.Axes, plt.Axes]:
    """Plot the merit order with the given method."""

    plt.rcParams.update({"mathtext.default": "regular"})
    plt.rc("text", usetex=False)
    plt.rc("font", family="serif")

    if mo_P is None:
        mo_P = get_merit_order(year=year, country=country, method=method, **mo_kwargs)

    mo_P = mo_P.copy()  # avoids modifying lru_cache
    # the unit of mo_P.marginal_emissions is kg
    mo_P.cumsum_capa /= 1000  # from MW to GW
    mo_P.capa /= 1000  # from MW to GW

    if ax is not None:
        fig = ax.get_figure()
    else:
        fig, ax = plt.subplots(1, figsize=(7, 3))

    ax_right = ax.twinx()

    color_left = "darkblue"
    color_right = "black"

    ax.step(
        x=hp.add_row_for_steps(mo_P.cumsum_capa),
        y=hp.add_row_for_steps(mo_P.marginal_cost),
        where="pre",
        label=r"pwl $c_p^m$",
        drawstyle="steps",
        color=color_left,
        linewidth=1.5,
    )

    ax_right.step(
        x=hp.add_row_for_steps(mo_P.cumsum_capa),
        y=hp.add_row_for_steps(mo_P.marginal_emissions),
        where="pre",
        label=r"pwl $\varepsilon_p$",
        drawstyle="steps",
        color=color_right,
        linewidth=0.5,
    )

    ax.set_xlabel(r"Net power [GW$_{el}$]")
    ax.set_ylabel(r"Marginal cost $c_p^m$" + "\n" + r"[€/$MWh_{el}$]")
    ax_right.set_ylabel(
        r"Marginal emissions $\varepsilon_p$" + "\n" + r"[$t_{CO_{2}eq}$/$MWh_{el}$]"
    )

    plt.xlim((0, mo_P.cumsum_capa.max()))
    ax.set_ylim(bottom=0, top=ylim_left)
    ax_right.set_ylim(bottom=0, top=ylim_right)

    ax.yaxis.label.set_color(color_left)
    ax.tick_params(axis="y", colors=color_left)
    ax.spines["left"].set_color(color_left)

    ax_right.yaxis.label.set_color(color_right)
    ax_right.tick_params(axis="y", colors=color_right)
    ax_right.spines["right"].set_color(color_right)

    alpha_value_for_fuels = _make_colored_background_for_fuel_types(ax, mo_P)

    if include_legend:
        _add_legend(mo_P, legend_fontsize, alpha_value_for_fuels)

    if include_histo:
        _add_histo(year, country, ax_right)

    plt.tight_layout()

    return fig, ax, ax_right


def _add_histo(year, country, ax_right):
    resi = get_residual_load(year=year, country=country) / 1000
    n, bins = np.histogram(resi, bins=20, density=True)
    ylim = ax_right.get_ylim()[1]
    max_loc = 0.15
    y = n * max_loc * (ylim / n.max())
    ax_right.fill_between(bins[1:], y, step="post", color="black", alpha=0.5)


def _add_legend(mo_P, legend_fontsize, alpha_value_for_fuels):
    fuels = mo_P.fuel_draf.unique()
    cdict = mp.TECH_COLORS
    legend_elements = [
        Patch(facecolor=cdict[f], edgecolor=cdict[f], alpha=alpha_value_for_fuels, label=f)
        for f in fuels
    ]
    leg = plt.legend(
        handles=legend_elements,
        bbox_to_anchor=(0.0, 1.01, 1.0, 0.102),
        loc="lower left",
        ncol=6,
        mode="expand",
        borderaxespad=0.0,
        fontsize=legend_fontsize,
        framealpha=1.0,
        handletextpad=0.5,
        edgecolor="inherit",
    )
    leg.get_frame().set_linewidth(0.5)


def _make_colored_background_for_fuel_types(ax, mo_P):
    alpha_value_for_fuels = 0.7
    for i, row in mo_P.iterrows():
        ax.axvspan(
            row["cumsum_capa"] - row["capa"],
            row["cumsum_capa"],
            facecolor=mp.TECH_COLORS[row["fuel_draf"]],
            linewidth=0,
            alpha=alpha_value_for_fuels,
            ymin=0,
            ymax=1,
        )
    return alpha_value_for_fuels


def cefs_scatter_plotly(
    year: int = 2019, freq: str = "60min", country: str = "DE", method: str = "MEF_PWL", **mo_kwargs
):
    """Optional interactive scatter plot. Works only if plotly is installed."""
    import plotly.express as px

    first_part, second_part = method.split("_")

    df = get_emissions(year=year, freq=freq, country=country, method=f"_{second_part}", **mo_kwargs)
    return px.scatter(
        df, y=f"{first_part}s", color="marginal_fuel", color_discrete_map=mp.TECH_COLORS
    )


def cefs_scatter(
    year=2019,
    freq: str = "60min",
    country: str = "DE",
    method: str = "MEF_PWL",
    figsize: Tuple = (8, 3),
    **mo_kwargs,
) -> None:
    """Plot the CEFs as scatter plot with colors refering to marginal power plant type."""
    _, second_part = method.split("_")

    df = get_emissions(year=year, freq=freq, country=country, method=f"_{second_part}", **mo_kwargs)

    df = df.reset_index().set_index(["index", "marginal_fuel"])["MEFs"].unstack()
    df.index.name = None
    df.plot(
        marker="o",
        markersize=2.5,
        figsize=figsize,
        linewidth=0,
        color=mp.get_tech_colors(df.keys()),
    )

    ax = plt.gca()
    ax.set(ylabel="Carbon emission factors\n[$g_{CO_{2}eq}$ / $kWh_{el}$]")
    ax.legend(ncol=6, loc="lower center", bbox_to_anchor=(0.5, 1), frameon=True)


def _small(s: str):
    return f"<span style='font-size:small;'>{s}</span>"


def xef_country_map(year: int = 2019, method: str = "XEF_PWL"):
    from iso3166 import countries
    import plotly.express as px

    df = pd.DataFrame([(k, v) for k, v in mp.EUROPE30.items()], columns=["iso_alpha2", "country"])
    df["iso_alpha3"] = df.iso_alpha2.apply(lambda x: countries.get(x).alpha3)
    df[method] = df.iso_alpha2.apply(
        lambda x: get_emissions(year=year, country=x, method=method).mean()
    )
    small_adder = _small("(unsupported countries in light blue)")
    fig = px.choropleth(
        df,
        locations="iso_alpha3",
        color=method,
        hover_name="country",
        scope="europe",
        color_continuous_scale="OrRd",
        labels={method: f"{method}<br>gCO2eq/kWh"},
        title=f"{year} mean {method} of supported countries<br>{small_adder}",
        width=700,
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        title={"y": 0.12, "x": 0.5, "xanchor": "center", "yanchor": "top"},
        coloraxis_colorbar=dict(xpad=0, x=0.95),
    )
    return fig
