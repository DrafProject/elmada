import logging
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

import pandas as pd

import elmada
from elmada import helper as hp
from elmada import paths

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.WARN)


def get_emissions(
    year: int,
    freq: str = "60min",
    country: str = "DE",
    method: str = "XEF_PP",
    additional_info: bool = False,
    cache: bool = True,
    **mo_kwargs,
) -> Union[pd.Series, pd.DataFrame]:
    """Returns dynamic carbon emisson factors in gCO2eq/kWh_el.

    $===

    Args:
        year: Year
        freq: Frequency
        country: Country
        method:
            ========  ===================================
            Method    Description
            ========  ===================================
            XEF_EP    Grid mix emission factors from historic generation data from ENTSOE-PY.
            XEF_SM    Grid mix emission factors from historic generation data from SMARD.
            XEF_PP    Grid mix emission factors from power plant list (PP-method).
            XEF_PWL   Grid mix emission factors approximated by piecewise linear approach (PWL-method).
            XEF_PWLv  XEF_PWL, but in validation mode.
            MEF_PP    Marginal power plant emission factors from power plant list (PP-method).
            MEF_PWL   Marginal power plant emission factors approximated by piecewise linear approach (PWL-method).
            MEF_PWLv  MEF_PWL, but in validation mode.
            ========  ===================================
        additional_info: If switched on, a Dataframe instead of a Series is returned.
        cache: If cache is used.
    """
    first_method_part, last_method_part = method.split("_")

    fp = paths.CACHE_DIR / f"{year}_{country}_{freq}_CEFs_{last_method_part}.h5"

    if cache and fp.exists() and not mo_kwargs:
        df = pd.read_hdf(fp)
    else:
        df = _make_emissions(
            year=year, freq=freq, country=country, method=last_method_part, **mo_kwargs
        )
        if cache:
            hp.write_array(df, fp)

    if additional_info:
        return df
    else:
        if first_method_part == "XEF":
            return df["XEFs"]
        else:
            return df["MEFs"]


def _make_emissions(year, freq, country, method, **mo_kwargs) -> pd.DataFrame:
    config = dict(year=year, freq=freq, country=country)

    if method == "EP":
        return elmada.el_entsoepy.prep_XEFs(**config)
    elif method == "SM":
        return elmada.el_smard.prep_XEFs(**config)
    elif method == "PP":
        return elmada.el_opsd.prep_CEFs(**config, **mo_kwargs)
    elif method in ["PWL", "PWLv"]:
        return elmada.el_EU_PWL_CEFs.prep_CEFs(
            **config, validation_mode=bool(method == "PWLv"), **mo_kwargs
        )
    else:
        raise RuntimeError(f"Method {method} not implemented.")


def get_merit_order(year: int, country: str = "DE", method: str = "PP", **kwargs) -> pd.DataFrame:
    if method == "PP":
        assert country == "DE", f"PP-method only works for Germany and not for {country}"
        return elmada.el_opsd.merit_order(year=year, **kwargs)
    elif method == "PWL":
        return elmada.el_EU_PWL_CEFs.merit_order(
            year=year, country=country, validation_mode=False, **kwargs
        )
    elif method == "PWLv":
        return elmada.el_EU_PWL_CEFs.merit_order(
            year=year, country=country, validation_mode=True, **kwargs
        )
    else:
        logger.error("`method` needs to be one of 'PP', 'PWL', 'PWLv'.")


def get_el_national_load(year: int, freq: str = "60min", country: str = "DE", **kwargs):
    return elmada.el_entsoepy.load_el_national_load(year=year, freq=freq, country=country, **kwargs)


def get_residual_load(year: int, freq: str = "60min", country: str = "DE", **kwargs) -> pd.Series:
    return elmada.el_entsoepy.prep_residual_load(year=year, freq=freq, country=country, **kwargs)


def get_el_national_generation(
    year: int, freq: str = "60min", country: str = "DE", source: str = "entsoe"
) -> pd.DataFrame:

    if source == "entsoe":
        return elmada.el_entsoepy.load_el_national_generation(year=year, freq=freq, country=country)
    else:
        raise RuntimeError("Currently, no source other than entsoe implemented.")


def get_prices(
    year: int,
    freq: str = "60min",
    country: str = "DE",
    method: str = "historic_entsoe",
    cache: bool = True,
    **mo_kwargs,
) -> pd.Series:
    """Returns the day-ahead spot-market electricity prices in €/MWh.

    method:
      ===============  ===========================
      Method           Description
      ===============  ===========================
      historic_entsoe  historic data from entsoe transparency platform.
      historic_smard   historic data from smard data platform (only for Germany).
      PP               from power plant list (PP-method).
      PWL              approximated by piecewise linear approach (PWL-method).
      PWLv             PWL-method, but in validation mode.
      ===============  ===========================

    WARNING: known data problems
        - (2015, DE, entsoe)-prices: data missing until Jan 6th
        - (2018, DE, entsoe)-prices: data missing from Sep 30th
    """

    # >> workaround due to bad data
    if year in [2015, 2018] and country == "DE" and method == "historic_entsoe":
        method = "historic_smard"
        logger.warning(
            f"The requested entsoe-data ({year}, {country}) "
            "is not complete. Smard-data is given to you instead."
        )
    # <<

    config = dict(year=year, freq=freq, country=country, cache=cache)

    if method == "historic_entsoe":
        return elmada.el_entsoepy.prep_dayahead_prices(**config)
    elif method == "historic_smard":
        return elmada.el_smard.prep_dayahead_prices(**config)
    elif method in ["PP", "PWL", "PWLv"]:
        df = get_emissions(**config, method=f"_{method}", additional_info=True, **mo_kwargs)
        return df["marginal_cost"]
    else:
        logger.error(f"method {method} not implemented.")
