from pathlib import Path

import pandas as pd

import elmada
from elmada import mappings as mp

MYDIR = Path(__file__).resolve().parent


def make_avgs() -> pd.DataFrame:
    return pd.Series(
        {
            (str(year), country, cef_type): int(
                elmada.get_emissions(year=year, country=country, method=f"{cef_type}_PWL").mean()
            )
            for year in range(2017, 2021)
            for country in mp.COUNTRIES_FOR_ANALYSIS
            for cef_type in ("MEF", "XEF")
        },
    ).unstack([0])


def save_expected_avgs() -> None:
    fp = MYDIR / "avgs.csv"
    if input("Do you really want to overwrite the data average table? (y/n)") == "y":
        make_avgs().to_csv(fp, header=True)
    else:
        print("Aborted.")


def read_expected_avgs() -> pd.Series:
    fp = MYDIR / "avgs.csv"
    return pd.read_csv(fp, index_col=[0, 1])
