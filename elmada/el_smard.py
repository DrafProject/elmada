import csv
import logging

import pandas as pd

from elmada import el_entsoepy as ep
from elmada import helper as hp
from elmada import paths

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.WARN)


# FUEL_RENAME_SMARD = {
#     "Wasserkraft[MWh]": "hydro",
#     "Biomasse[MWh]": "biomass",
#     "Kernenergie[MWh]": "nuclear",
#     "Braunkohle[MWh]": "lignite",
#     "Steinkohle[MWh]": "coal",
#     "Erdgas[MWh]": "gas",
#     "Sonstige Konventionelle[MWh]": "other_conv",
#     "Pumpspeicher[MWh]": "pumped_hydro",
#     "Sonstige Erneuerbare[MWh]": "other_RES",
#     "Wind Offshore[MWh]": "wind_offshore",
#     "Wind Onshore[MWh]": "wind_onshore",
#     "Photovoltaik[MWh]": "solar",
# }

# FUELS_SMARD = set(FUEL_RENAME_SMARD.values())


# def load_el_national_generation(year):
#     assert year in range(2000, 2100), f"{year} is not a valid year"

#     fp_raw = paths.DATA_DIR / f"smard/DE_Realisierte Erzeugung_{year}_SMARD.csv"

#     with open(fp_raw, "r") as f:
#         reader = csv.reader(f, delimiter=",")
#         row1 = next(reader)  # gets the first line

#     # translate to US-Numberformat:
#     def converter_func(x):
#         return float(x.replace("-", "NaN").replace(".", "").replace(",", "."))

#     converters = {i: converter_func for i in range(len(row1))}

#     el_generation = pd.read_csv(
#         fp_raw, converters=converters, usecols=range(2, len(row1))
#     )  # in [MWh]
#     el_generation = el_generation.rename(columns=FUEL_RENAME_SMARD)

#     return el_generation


# def load_el_national_load(
#     year: int, freq: str = "15min", country: str = "DE", cache: bool = True
# ) -> pd.Series:

#     assert year in range(2000, 2100), f"{year} is not a valid year"
#     assert freq in ["15min"], f"{freq} is not a valid freq"
#     assert country == "DE", "smard provides data only for DE!"

#     fp = paths.CACHE_DIR / f"{year}_{freq}_{country}_load_smard.h5"

#     if cache and fp.exists():
#         ser = pd.read_hdf(fp)

#     else:
#         with open(fp, "r") as f:
#             reader = csv.reader(f, delimiter=";")
#             row1 = next(reader)  # gets the first line

#         # translate to US number format:
#         def converter_func(x):
#             return float(x.replace("-", "NaN").replace(".", "").replace(",", "."))

#         converters = {i: converter_func for i in range(len(row1))}

#         fp_raw = paths.DATA_DIR / f"smard/DE_Realisierter Stromverbrauch_{year}_SMARD.csv"
#         ser = pd.read_csv(fp_raw, sep=";", converters=converters, usecols=[2])  # in [MWh]
#         ser.fillna(ser.mean(), inplace=True)
#         if cache:
#             hp.write(ser, fp)

#     hp.warn_if_incorrect_index_length(ser, year, freq)
#     return ser


# def prep_XEFs(year: int, freq: str = "60min", country: str = "DE") -> pd.DataFrame:

#     assert year in range(2000, 2100), f"{year} is not a valid year"
#     assert freq in ["15min", "60min"], f"{freq} is not a valid freq"
#     assert country == "DE", "smard provides only for DE!"

#     gen = load_el_national_generation(year=year)

#     specific_emissions = ep.load_el_national_specific_emissions()

#     shares = gen.copy()
#     gen["sum"] = gen.sum(axis=1)

#     for f in FUELS_SMARD:
#         shares[f] = gen[f] / gen["sum"]

#     shares["sum"] = shares.sum(axis=1)

#     ser = pd.Series(0, index=gen.index)
#     ser.index.name = "T"
#     for f in FUELS_SMARD:
#         ser += shares[f] * specific_emissions["value"][f]

#     ser.fillna(ser.mean(), inplace=True)

#     if freq == "60min":
#         ser = hp.downsample(ser, year=year, aggfunc="mean")

#     hp.warn_if_incorrect_index_length(ser, year, freq)
#     df = ser.rename("XEFs").to_frame()
#     return df


def prep_dayahead_prices(
    year: int, freq: str = "60min", country: str = "DE", cache: bool = True
) -> pd.Series:

    assert year in range(2000, 2100), f"{year} is not a valid year"
    assert country == "DE", "smard provides only for DE!"

    fp = paths.CACHE_DIR / f"{year}_{freq}_{country}_dayahead_c_el_smard.parquet"

    if cache and fp.exists():
        ser = hp.read(fp)

    else:
        import re

        fp_raw = paths.DATA_DIR / f"smard/DE_Grosshandelspreise_{year}_SMARD.csv"

        with open(fp_raw, "r") as f:
            reader = csv.reader(f, delimiter=";")
            row1 = next(reader)  # gets the first line

        def convert(x):
            x = re.sub(pattern="-\B", repl="NaN", string=x)
            x = x.replace(".", "").replace(",", ".")
            return float(x)

        converter = {i: convert for i in range(len(row1))}

        df = pd.read_csv(
            fp_raw, sep=";", converters=converter, usecols=range(2, len(row1))
        )  # in [MWh]
        df = df.reset_index(drop=True)
        df = df.fillna(df.mean())

        # add a merged column
        df["DE_merged"] = 0

        if year < 2018:
            df["DE_merged"] = df["Deutschland/Österreich/Luxemburg[Euro/MWh]"]

        elif year == 2018:
            import warnings

            warnings.filterwarnings(
                "ignore",
                message="A value is trying to be set on a copy of a slice from a DataFrame",
            )
            df.loc[:6552, "DE_merged"] = df.loc[:6552, "Deutschland/Österreich/Luxemburg[Euro/MWh]"]
            df.loc[6552:, "DE_merged"] = df.loc[6552:, "Deutschland/Luxemburg[Euro/MWh]"]

        elif year > 2018:
            df["DE_merged"] = df["Deutschland/Luxemburg[Euro/MWh]"]

        ser = df["DE_merged"]
        if cache:
            hp.write(ser, fp)

    start_freq = hp.estimate_freq(ser)

    ser = hp.resample(ser, year=year, start_freq=start_freq, target_freq=freq)
    if start_freq != freq:
        logger.warning(f"Dayahead_prices were resampled from {start_freq} to {freq}")

    hp.warn_if_incorrect_index_length(ser, year, freq)
    return ser
