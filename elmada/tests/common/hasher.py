import hashlib
from pathlib import Path

from numpy.core.arrayprint import str_format

import elmada
import pandas as pd
from elmada import mappings as mp

DATA_HASH_TABLE_PATH = Path(__file__).resolve().parent / "data_hashes.csv"


def read_target_cef_hashes() -> pd.Series:
    return pd.read_csv(DATA_HASH_TABLE_PATH, index_col=[0, 1], squeeze=True)


def save_target_cef_hashes() -> None:
    if input("Do you really want to overwrite the data hash table? (y/n)") == "y":
        make_cef_hashes().to_csv(DATA_HASH_TABLE_PATH, header=True)
    else:
        print("Aborted.")


def make_cef_hashes() -> pd.Series:
    ser = pd.Series(
        {
            (year, country): get_cef_hash(year, country)
            for year in range(2017, 2021)
            for country in mp.COUNTRIES_FOR_ANALYSIS
        },
        name="hash",
    )

    ser.index.names = ["year", "country"]
    return ser


def get_cef_hash(year, country) -> str:
    df = elmada.get_emissions(
        year=year, freq="60min", country=country, additional_info=True, method="_PWL"
    )
    return get_hash(df)


def get_hash(df) -> str_format:
    return hashlib.sha256(pd.util.hash_pandas_object(df, index=True).values).hexdigest()[:10]
