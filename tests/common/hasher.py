import hashlib
from pathlib import Path

from numpy.core.arrayprint import str_format

import elmada
import pandas as pd
from elmada import mappings as mp

HASH_DIR = Path(__file__).resolve().parent
FILE_FMT = "{which}_hashes.csv"


def read_expected_hashes(which: str) -> pd.Series:
    fp = HASH_DIR / FILE_FMT.format(which=which)
    return pd.read_csv(fp, index_col=[0, 1], squeeze=True)


def save_expected_hashes(which: str) -> None:
    fp = HASH_DIR / FILE_FMT.format(which=which)
    if input("Do you really want to overwrite the data hash table? (y/n)") == "y":
        make_hashes(which=which).to_csv(fp, header=True)
    else:
        print("Aborted.")


def make_hashes(which) -> pd.Series:

    if which == "CEF":
        func = elmada.get_emissions
        kwargs = dict(freq="60min", method="_PWL", cache=True)

    elif which == "GEN":
        func = elmada.get_el_national_generation
        kwargs = dict(freq="60min")

    else:
        raise ValueError("`which` must be 'CEF' or 'GEN'.")

    return make_year_country_hashes(func=func, kwargs=kwargs)


def make_year_country_hashes(func, kwargs) -> pd.Series:
    ser = pd.Series(
        {
            (year, country): get_hash(func(year=year, country=country, **kwargs))
            for year in range(2017, 2021)
            for country in mp.COUNTRIES_FOR_ANALYSIS
        },
        name="hash",
    )
    ser.index.names = ["year", "country"]
    return ser


def get_hash(df) -> str_format:
    return hashlib.sha256(pd.util.hash_pandas_object(df, index=True).values).hexdigest()[:10]
