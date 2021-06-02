import logging
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from elmada import paths

# from scipy import stats

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.CRITICAL)


def make_symlink_to_cache(where: Optional[Path] = None):
    """Creates a symbolic link to the cache directory for easy access."""

    parent_dir_for_link = paths.BASE_DIR if where is None else Path(where)

    link_dir = parent_dir_for_link / "cache"

    cache_dir = paths.CACHE_DIR
    link_dir.symlink_to(target=cache_dir, target_is_directory=True)
    print(f"Symbolic link created: {link_dir} --> {cache_dir}")


def delete_cache(filter_str: str = "*") -> None:
    """Deletes parts or all of the cache directory.

    Unless `filter_str` is '*' only files are selected that contain the `filter_string` somewhere
    in the filename.
    """

    if filter_str == "*":
        s = "*"

    else:
        s = f"*{filter_str}*"

    files = list(paths.CACHE_DIR.glob(f"{s}"))
    lenf = len(files)

    if lenf == 0:
        print(f"No file found containing '{filter_str}'.")

    else:
        print(f"{lenf} files containing '{filter_str}':")

        for f in files:
            size = sizeof_fmt(f.stat().st_size)
            print(f"\t{size:>5}{f.name}")

        if confirm_deletion(lenf):
            for f in files:
                f.unlink()
            print(f"{lenf} files deleted")

        else:
            print("No files deleted")


def confirm_deletion(nfiles: int) -> bool:
    return input(f"Do you really want to delete these {nfiles} files? (y/n)") == "y"


def print_error(series1: pd.Series, series2: pd.Series) -> None:
    err = abs(series1 - series2)
    err_rel = err / series1
    print(f"relative error = {err_rel.mean():.2%}, absolute error= {err.mean():.2f} t CO2/MWh.")


def add_row_for_steps(ser: pd.Series) -> pd.Series:
    """Adds an initial row in the Series for plotting steps. This way the first step does not
     disappear when choosing option `pre`.
    """
    return ser.append(pd.Series({-1: 0})).sort_index()


def sizeof_fmt(num: float, suffix: str = "B") -> str:
    """Returns the short version of the storage size of e.g. digital information.

    Example:
        sizeof_fmt(5000) -> 5.0 KB

    Idea from https://stackoverflow.com/questions/1094841
    """
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if abs(num) < 1000.0:
            return f"{num:.1f} {unit}{suffix}"
        num /= 1000.0
    return f"{num:.1f} Y{suffix}"


def freq_to_hours(freq: str) -> float:
    """E.g.:
        '60min' -> 1.0
        '30min' -> 0.5
    """
    assert freq in ["60min", "30min", "15min"]
    return float(freq[:2]) / 60


def int_to_datetime(freq: str, year: int, pos: int) -> "datetime":
    dtindex = make_datetimeindex(year=year, freq=freq)
    return dtindex[pos]


def datetime_to_int(freq: str, year: int, month: int, day: int) -> int:
    """Returns the index location in a whole-year date-time-index for the given date."""
    dtindex = make_datetimeindex(year=year, freq=freq)
    i = datetime(year, month, day)
    return dtindex.get_loc(i)


def is_correct_length(df: Union[pd.DataFrame, pd.Series], year: int, freq: str):
    len_dt = len(make_datetimeindex(year=year, freq=freq))
    len_inp = len(df)
    return len_dt == len_inp


def write_array(data: Union[pd.Series, pd.DataFrame], fp: Union[Path, str]) -> None:
    """Standardized way of writing arrays in draf.

    Args:
        data: Must be either pandas.Series or pandas.DataFrame.
        fp: Filepath of a .h5 or .csv file.
    """

    fp = Path(fp)

    if fp.suffix == ".h5":
        data.to_hdf(fp, key="default", mode="w")

    elif fp.suffix == ".csv":
        data.to_csv(fp, header=True, index=False)

    else:
        raise RuntimeError(f"suffix {fp.suffix} not supported")


def warn_if_incorrect_index_length(
    df: Union[pd.DataFrame, pd.Series], year: int, freq: str
) -> None:
    len_dt = len(make_datetimeindex(year=year, freq=freq))
    len_inp = len(df)
    match = len_dt == len_inp
    if not match:
        logger.warning(f"Length mismatch: An object has {len_inp} instead of {len_dt}.")


@lru_cache(maxsize=16)
def make_datetimeindex(year: int = 2019, freq: str = "60min", tz: str = None) -> pd.DatetimeIndex:
    """Returns a whole-year date-time-index in desired resolution."""
    date_start = f"01.01.{year}  00:00:00"
    date_end = f"31.12.{year}  23:59:00"
    return pd.date_range(date_start, date_end, freq=freq, tz=tz)


def resample(
    df: Union[pd.Series, pd.DataFrame],
    year: int,
    start_freq: str,
    target_freq: Optional[str],
    aggfunc: str = "mean",
) -> Union[pd.Series, pd.DataFrame]:
    """Resamples data from a start frequency to a target frequency."""
    if (target_freq is None) or (start_freq == target_freq):
        return df
    else:
        if int_from_freq(start_freq) > int_from_freq(target_freq):
            func = upsample
        else:
            func = downsample

        return func(
            df=df, year=year, start_freq=start_freq, target_freq=target_freq, aggfunc=aggfunc
        )


def downsample(
    df: Union[pd.Series, pd.DataFrame],
    year: int,
    start_freq: str = "15min",
    target_freq: str = "60min",
    aggfunc: str = "mean",
) -> Union[pd.Series, pd.DataFrame]:
    """Downsampling for cases where start frequency is higher then target frequency.

    Args:
        df: Series or Dataframe
        year: Year
        start_freq: Time resolution of given data.
        target_freq: Time resolution of returned data.
        aggfunc:  in {"mean", "sum"}
    """

    df = df.copy()
    df.index = make_datetimeindex(year, freq=start_freq)

    resampler = df.resample(target_freq)

    if aggfunc == "sum":
        df = resampler.sum()
    elif aggfunc == "mean":
        df = resampler.mean()
    else:
        raise RuntimeError(f"aggfunc {aggfunc} not valid")

    df = df.reset_index(drop=True)

    if isinstance(df, pd.Series) and isinstance(df.name, str):
        df.name = df.name.replace(start_freq, target_freq)

    warn_if_incorrect_index_length(df, year, target_freq)
    return df


def upsample(
    df: Union[pd.Series, pd.DataFrame],
    year: int,
    start_freq: str = "60min",
    target_freq: str = "15min",
    aggfunc: str = "mean",
) -> Union[pd.Series, pd.DataFrame]:
    """Upsampling for cases where start frequency is lower then target frequency.

    Args:
        df: Series or Dataframe
        year: Year
        start_freq: Time resolution of given data.
        target_freq: Time resolution of returned data.
        aggfunc: Either 'mean' or 'sum', e.g. use `mean` for power and `sum` for aggregated energy.
    """
    df = df.copy()
    df.index = make_datetimeindex(year, freq=start_freq)
    df = df.resample(target_freq).pad()
    convert_factor = int_from_freq(start_freq) / int_from_freq(target_freq)
    if aggfunc == "sum":
        df /= convert_factor

    df = df.reset_index(drop=True)
    df = _append_rows(df, convert_factor=convert_factor)

    if isinstance(df, pd.Series) and isinstance(df.name, str):
        df.name = df.name.replace(start_freq, target_freq)

    warn_if_incorrect_index_length(df, year, target_freq)
    return df


def _append_rows(
    df: Union[pd.Series, pd.DataFrame], convert_factor: float
) -> Union[pd.Series, pd.DataFrame]:
    length = len(df)
    if isinstance(df, pd.DataFrame):
        addon_data = [df.iloc[length - 1]]
    elif isinstance(df, pd.Series):
        addon_data = df.iloc[length - 1]
    else:
        raise RuntimeError(f"unsupported type {type(df)}")

    number_of_lines = int(convert_factor - 1)
    new_index = [length + i for i in range(number_of_lines)]

    class_of_df = type(df)
    line = class_of_df(data=addon_data, index=new_index)  # new Series OR Dataframe.
    df = df.append(line).sort_index().reset_index(drop=True)
    return df


def z_score(df: Union[pd.Series, pd.DataFrame]) -> Union[pd.Series, pd.DataFrame]:
    """Returns the standard score for all data points.
    Info: The z-score tells how many standard deviations below or above the population mean a raw
     score is.
    """
    return (df - df.mean()) / df.std(ddof=0)


def remove_outlier(
    df: Union[pd.Series, pd.DataFrame], zscore_threshold: float = 2.698
) -> Union[pd.Series, pd.DataFrame]:
    """Detects and removes outliers of Dataframes or Series.

    Note: The default z-score of 2.698 complies to the boxplot standard (1,5*IQR-rule).
     (see https://towardsdatascience.com/5e2df7bcbd51)
    """
    df = df.copy()

    # see
    # https://stackoverflow.com/questions/23451244/how-to-zscore-normalize-pandas-column-with-nans

    if isinstance(df, pd.DataFrame):
        for k in df:
            df[k] = remove_outlier(df[k], zscore_threshold)
        # df[(np.abs(stats.zscore(df)) > zscore_threshold).any(axis=1)] = np.nan

    if isinstance(df, pd.Series):
        outliers = np.abs(z_score(df)) > zscore_threshold
        n_outliers = outliers.sum()
        df[outliers] = np.nan
        outlier_share = n_outliers / len(df)
        outlier_treshold = 0.1
        if outlier_share > outlier_treshold:
            logger.warning(
                f"{outlier_share:.2%} (more than {outlier_treshold:.0%}) of the data were outliers"
            )
        logger.info(f"{n_outliers} datapoints where removed in {df.name}")
        # df[(np.abs(stats.zscore(df)) > zscore_threshold)] = np.nan

    return df


def fill_outlier_and_nan(
    df: Union[pd.Series, pd.DataFrame], zscore_threshold: int = 3, method: str = "linear",
) -> Union[pd.Series, pd.DataFrame]:

    df = remove_outlier(df, zscore_threshold)

    if method is "linear":
        df = df.interpolate(method="linear")
    elif method == "fill":
        df = df.fillna(method="bfill").fillna(method="ffill")

    return df


def estimate_freq(data: Union[List, pd.Series, pd.DataFrame]) -> str:
    """Estimate the correct frequency by the length of the yearly data-set."""
    data_len = len(data)
    minutes_per_year = 8760 * 60
    tolerance = 0.2

    for step_length_in_minutes in [60, 30, 15]:
        error = abs(data_len * step_length_in_minutes / minutes_per_year - 1)
        if error < tolerance:
            return f"{step_length_in_minutes}min"

    raise RuntimeError(f"Data contains {data_len} datapoints. It cannot be matched to a frequency.")


def int_from_freq(freq: str) -> int:
    """E.g. '15min' -> 15"""
    return int(freq[:2])
