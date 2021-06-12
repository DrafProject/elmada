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
    cache: bool = True,
    use_datetime: bool = False,
    **mo_kwargs,
) -> Union[pd.Series, pd.DataFrame]:
    """Returns dynamic carbon emisson factors in gCO2eq/kWh_el and optional data.

    Args:
        year: Year
        freq: Frequency, e.g. '60min' or '15min'
        country: alpha-2 country code, e.g. 'DE'
        method: A method string that consists of two parts joined by an underscore. The first
            part is the type of emission factor. Use 'XEF' for grid mix emission factors and
            'MEF' for marginal emission factors. The second part determines the calculation method
            or data sources. 'EP' stands for ENTSO-E, 'PP' for power plant method, 'PWL' for piecewise
            linear method, 'PWLv' for the piecewise linear method in validation mode.
            For PP, PWL, and PWLv, the first can be omitted ('_PP', '_PWL', '_PWLv') to return
            a DataFrame including the columns 'residual_load', 'total_load', 'marginal_fuel',
            'efficiency', 'marginal_cost', 'MEFs', 'XEFs'.
            The following combinations are possible:

            | Method   | Description                              |
            | -------- | ---------------------------------------- |
            | XEF_EP   | Series: XEFs using ENTSO-E data          |
            | XEF_PP   | Series: XEFs using PP method             |
            | XEF_PWL  | Series: XEFs using PWL method            |
            | XEF_PWLv | Series: XEFs using PWLv method           |
            | MEF_PP   | Series: MEFs from PP method              |
            | MEF_PWL  | Series: MEFs using PWL method            |
            | MEF_PWLv | Series: MEFs using PWLv method           |
            | _PP      | Dataframe: extended data for PP method   |
            | _PWL     | Dataframe: extended data for PWL method  |
            | _PWLv    | Dataframe: extended data for PWLv method |

        cache: If cache is used.
        use_datetime: If True, the index is a timezone agnostic datetime. If False, the index is
            0, 1, 2, etc.
        **mo_kwargs: Keyword arguments for merit order creation such as 'overwrite_carbon_tax',
            'efficiency_per_plant', 'emission_data_source'.
    """
    first_method_part, last_method_part = method.split("_")

    fp = paths.CACHE_DIR / f"{year}_{country}_{freq}_CEFs_{last_method_part}.parquet"

    if cache and fp.exists() and not mo_kwargs:
        df = hp.read(fp)
    else:
        df = _make_emissions(
            year=year, freq=freq, country=country, method=last_method_part, **mo_kwargs
        )
        if cache:
            hp.write(df, fp)

    if use_datetime:
        df.index = hp.make_datetimeindex(year=year, freq=freq)

    if first_method_part in ("XEF", "MEF"):
        return df[first_method_part + "s"]
    else:
        return df


def _make_emissions(year, freq, country, method, **mo_kwargs) -> pd.DataFrame:
    config = dict(year=year, freq=freq, country=country)

    if method == "EP":
        return elmada.from_entsoe.prep_XEFs(**config)
    # elif method == "SM":
    #     return elmada.from_smard.prep_XEFs(**config)
    elif method == "PP":
        return elmada.from_opsd.prep_CEFs(**config, **mo_kwargs)
    elif method in ["PWL", "PWLv"]:
        is_vmode = bool(method == "PWLv")
        return elmada.eu_pwl.prep_CEFs(validation_mode=is_vmode, **config, **mo_kwargs)
    else:
        raise ValueError(f"Method {method} not implemented.")


def get_prices(
    year: int,
    freq: str = "60min",
    country: str = "DE",
    method: str = "hist_EP",
    cache: bool = True,
    **mo_kwargs,
) -> pd.Series:
    """Returns the day-ahead spot-market electricity prices in €/MWh.

    Args:
        year: Year
        freq: Frequency, e.g. '60min' or '15min'
        country: alpha-2 country code, e.g. 'DE'
        method: 'PP' stands for power plant method, 'PWL' stands for piecewise
            linear method, 'PWLv' stands for the piecewise linear method in validation mode.

            | Method  | Description                                         |
            | ------- | --------------------------------------------------- |
            | PP      | Using PP method                                     |
            | PWL     | Using PWL method                                    |
            | PWLv    | Using PWLv method                                   |
            | hist_EP | Using historic ENTSO-E data                         |
            | hist_SM | Using historic Smard data only for DE, (2015, 2018  |

    Known data issues:
        - (2015, DE, entsoe)-prices: data missing until Jan 6th
        - (2018, DE, entsoe)-prices: data missing from Sep 30th
    """

    # >> Workaround due to missing data for DE
    if year in [2015, 2018] and country == "DE" and method == "hist_EP":
        method = "hist_SM"
        logger.warning(
            f"The requested entsoe-data ({year}, {country}) is not complete. "
            f"Smard-data is given to you instead."
        )
    # <<

    config = dict(year=year, freq=freq, country=country, cache=cache)

    if method == "hist_EP":
        return elmada.from_entsoe.prep_dayahead_prices(**config)
    elif method == "hist_SM":
        return elmada.from_smard.prep_dayahead_prices(**config)
    elif method in ["PP", "PWL", "PWLv"]:
        df = get_emissions(method=f"_{method}", **config, **mo_kwargs)
        return df["marginal_cost"]
    else:
        raise ValueError(f"Method '{method}' not implemented.")


def get_merit_order(year: int, country: str = "DE", method: str = "PP", **kwargs) -> pd.DataFrame:
    """Returns the merit order.

    Args:
        year: Year
        country: alpha-2 country code, e.g. 'DE'
        method: One of 'PP' (power plant method), 'PWL' (piecewise
            linear method), 'PWLv' (piecewise linear method in validation mode).
        **kwargs: keyword arguments for merit order function depending on `method`.
    """
    if method == "PP":
        assert country == "DE", f"PP-method only works for Germany and not for {country}"
        return elmada.from_opsd.merit_order(year=year, **kwargs)
    elif method == "PWL":
        return elmada.eu_pwl.merit_order(
            year=year, country=country, validation_mode=False, **kwargs
        )
    elif method == "PWLv":
        return elmada.eu_pwl.merit_order(year=year, country=country, validation_mode=True, **kwargs)
    else:
        raise ValueError("`method` needs to be one of ['PP', 'PWL', 'PWLv'].")


def get_residual_load(year: int, freq: str = "60min", country: str = "DE", **kwargs) -> pd.Series:
    return elmada.from_entsoe.prep_residual_load(year=year, freq=freq, country=country, **kwargs)


def get_el_national_generation(year: int, freq: str = "60min", country: str = "DE") -> pd.DataFrame:
    return elmada.from_entsoe.load_el_national_generation(year=year, freq=freq, country=country)


# TODO: add get_merit_order()
