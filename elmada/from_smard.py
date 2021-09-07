import logging
import warnings

import pandas as pd

from elmada import helper as hp
from elmada import paths

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.WARN)


def prep_dayahead_prices(
    year: int, freq: str = "60min", country: str = "DE", cache: bool = True
) -> pd.Series:

    assert year in range(2000, 2100), f"{year} is not a valid year"
    assert country == "DE", "Smard is only used for Germany!"

    fp = paths.CACHE_DIR / f"{year}_{freq}_{country}_dayahead_c_el_smard.parquet"

    if cache and fp.exists():
        ser = hp.read(fp)

    else:
        fp_raw = paths.DATA_DIR / f"smard/Day-ahead_prices_{year}.csv"
        df = pd.read_csv(
            fp_raw,
            sep=";",
            usecols=["Germany/Luxembourg[€/MWh]", "Germany/Austria/Luxembourg[€/MWh]"],
            na_values="-",
        )
        df = df.reset_index(drop=True)
        df = df.fillna(df.mean())

        # add a merged column
        df["DE_merged"] = 0

        if year < 2018:
            df["DE_merged"] = df["Germany/Austria/Luxembourg[€/MWh]"]

        elif year == 2018:

            warnings.filterwarnings(
                "ignore",
                message="A value is trying to be set on a copy of a slice from a DataFrame",
            )
            df.loc[:6552, "DE_merged"] = df.loc[:6552, "Germany/Austria/Luxembourg[€/MWh]"]
            df.loc[6552:, "DE_merged"] = df.loc[6552:, "Germany/Luxembourg[€/MWh]"]

        elif year > 2018:
            df["DE_merged"] = df["Germany/Luxembourg[€/MWh]"]

        ser = df["DE_merged"]
        if cache:
            hp.write(ser, fp)

    start_freq = hp.estimate_freq(ser)

    ser = hp.resample(ser, year=year, start_freq=start_freq, target_freq=freq)
    if start_freq != freq:
        logger.warning(f"Dayahead_prices were resampled from {start_freq} to {freq}")

    hp.warn_if_incorrect_index_length(ser, year, freq)
    return ser
