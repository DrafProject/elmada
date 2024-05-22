import logging
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple, Union

import entsoe
import numpy as np
import pandas as pd

from elmada import exceptions
from elmada import helper as hp
from elmada import mappings as mp
from elmada import paths

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.WARN)


def prep_XEFs(year: int = 2019, freq: str = "60min", country: str = "DE") -> pd.DataFrame:
    """Prepare grid mix emission factors from historic generation."""
    assert year in range(2000, 2100), f"{year} is not a valid year"
    assert freq in ["15min", "60min"], f"{freq} is not a valid freq"
    assert country in mp.EUROPE_COUNTRIES

    shares_TF = prep_shares(year, freq, country)
    spec_emissions = load_el_national_specific_emissions()
    if country in spec_emissions:
        used_country = country
    else:
        used_country = "EU28"
        logger.warning(
            f"Country {country} not in Tranberg table for specific emission factors. "
            "EU28 average is used."
        )
    ce_F = spec_emissions[used_country]
    x = set(shares_TF.keys()) & set(ce_F.keys())
    ce_T = shares_TF[x] @ ce_F[x]
    ce_T = ce_T.fillna(ce_T.mean())

    hp.warn_if_incorrect_index_length(ce_T, year, freq)
    df = ce_T.rename("XEFs").to_frame()
    return df


def _get_client() -> entsoe.EntsoePandasClient:
    return entsoe.EntsoePandasClient(api_key=hp.get_api_key("entsoe"))


def _get_timestamps(year: int, tz: str) -> Tuple:
    start = pd.Timestamp(f"{year}0101", tz=tz)
    end = pd.Timestamp(f"{year+1}0101", tz=tz)
    return start, end


def _get_empty_installed_generation_capacity_df(ensure_std_techs: bool) -> pd.DataFrame:
    if ensure_std_techs:
        return pd.DataFrame(index=mp.DRAF_FUELS, columns=[""]).T
    else:
        raise exceptions.NoDataError("no Data")


def load_installed_generation_capacity(
    year: int = 2019, country: str = "DE", cache: bool = True, ensure_std_techs: bool = False
) -> pd.DataFrame:
    """Returns a dataframe with installed generation capacity fuel type dependent on year and
    country.
    """

    fp = paths.mode_dependent_cache_dir() / f"{year}_{country}_installedGen_entsoe.parquet"
    warning = f"No installed generation capacity data available for {year}, {country}"

    if cache and fp.exists():
        df = hp.read(fp, squeeze=False)
    else:
        try:
            df = _query_installed_generation_capacity(year, country)

            if df.empty:
                logger.warning(f"{warning}: ENTSO-E returned an empty dataframe.")
                return _get_empty_installed_generation_capacity_df(ensure_std_techs)

            if cache:
                hp.write(df, fp)

        except (entsoe.exceptions.NoMatchingDataError, KeyError) as e:
            logger.error(f"{e}: {warning}")
            return _get_empty_installed_generation_capacity_df(ensure_std_techs)

    if ensure_std_techs:
        df = aggregate_to_standard_techs(df)

    return df


def _query_installed_generation_capacity(year, country) -> pd.DataFrame:
    client = _get_client()
    tz = get_timezone(country)
    start, end = _get_timestamps(year=year, tz=tz)
    df = client.query_installed_generation_capacity(
        start=start, end=end, country_code=country, psr_type=None
    )
    return df


def aggregate_to_standard_techs(df) -> pd.DataFrame:
    for i in ["other_conv", "other_RES"]:
        if i not in df:
            df[i] = 0

    df = df.rename(columns=mp.FUEL_RENAME)

    for k, v in mp.FUEL_AGGREGATION.items():
        try:
            df[v] = df[v].add(df.pop(k), fill_value=0)
        except KeyError as e:
            logger.debug(f"KeyError: {e}")

    order = [k for k in mp.DRAF_FUELS if k in df.keys()]
    return df[order]


def load_el_national_generation(
    year: int = 2019,
    country: str = "DE",
    freq: Optional[str] = "15min",
    cache: bool = True,
    split_queries: bool = True,
    ensure_std_techs: bool = True,
    ensure_std_index: bool = True,
    ensure_positive: bool = True,
    ensure_non_zero_sum: bool = True,
    fillna: bool = True,
    resample: bool = True,
) -> pd.DataFrame:
    assert year in range(2000, 2100), f"{year} is not a valid year"
    assert freq in [None, "15min", "30min", "60min"], f"{freq} is not a valid frequency"
    assert country in mp.EUROPE_COUNTRIES

    fp = paths.mode_dependent_cache_dir(year, country) / f"{year}_{country}_gen_entsoe.parquet"

    if cache and fp.exists():
        df = hp.read(fp)

    else:
        df = _query_generation(year, country, split_queries)

        if cache:
            hp.write(df, fp)

    data_freq = hp.estimate_freq(df)

    if ensure_std_index:
        idx = hp.make_datetimeindex(year, data_freq, tz=df.index.tz)
        df = df.reindex(idx)
        df = df.reset_index(drop=True)

    if ensure_std_techs:
        df = aggregate_to_standard_techs(df)

    if ensure_positive:
        # set negative values as missing values e.g. for HU and NL in 2019
        df[df < 0] = np.nan

    if ensure_non_zero_sum:
        df[df.sum(1) == 0.0] = np.nan

    if fillna:
        df = fill_special_missing_data_points_for_gen(df=df, country=country, year=year)
        df = df.ffill().bfill()

    if resample:
        df = hp.resample(df, year=year, start_freq=data_freq, target_freq=freq)

    return df


def _query_generation(year, country, split_queries) -> pd.DataFrame:
    client = _get_client()
    tz = get_timezone(country)
    if split_queries:
        df = _query_generation_monthly(year, country, client, tz)
    else:
        df = _query_generation_yearly(year, country, client, tz)
    return df


def _query_generation_yearly(year, country, client, tz) -> pd.DataFrame:
    try:
        start, end = _get_timestamps(year=year, tz=tz)
        df = client.query_generation(start=start, end=end, country_code=country)
    except (entsoe.exceptions.NoMatchingDataError, KeyError) as e:
        err_message = f"{e}: entsoe-client has no geneneration data found for {year, country}"
        logger.error(err_message)
        raise exceptions.NoDataError(err_message)
    return df


def fill_special_missing_data_points_for_gen(
    df: pd.DataFrame, country: str, year: int
) -> pd.DataFrame:
    if year == 2019 and country == "NL":
        logger.warning(f"No Data for 2019-01-01, NL. --> Data of next sunday 2019-01-06 is given.")
        st = hp.datetime_to_int("15min", 2019, 1, 6)
        df.iloc[:96] = df.iloc[st : st + 96].values

    if year == 2018 and country == "NL":
        logger.warning(f"No Data after 2018-12-31 23:00, NL. --> Data of previous hour is given.")
        df.iloc[35036:35040] = df.iloc[35032:35036].values

    if year == 2018 and country == "LT":
        logger.warning(f"1 outlier for {year}, {country}, other_conv/Other removed.")
        try:
            df["other_conv"] = hp.remove_outlier(df["other_conv"], zscore_threshold=10)
        except KeyError:
            df["Other"] = hp.remove_outlier(df["Other"], zscore_threshold=10)

    if year == 2018 and country == "LT":
        logger.warning(f"3 outlier for {year}, {country}, solar/Solar removed.")
        try:
            df["solar"] = hp.remove_outlier(df["solar"], zscore_threshold=10)
        except KeyError:
            df["Solar"] = hp.remove_outlier(df["Solar"], zscore_threshold=10)

    return df


def _query_generation_monthly(year, country, client, tz) -> pd.DataFrame:
    logger.warning(f"Querying generation data from entsoe for {country}: this may take minutes.")
    logger.info(f"Loading 12 month of electrcity generation individually:")

    d = {}
    for month in range(1, 13):
        start, end = _get_timestamps_for_month(year, tz, month)

        try:
            logger.warning(f"Loading month {month} / 12")
            d[month] = client.query_generation(start=start, end=end, country_code=country)
        except (entsoe.exceptions.NoMatchingDataError, KeyError) as e:
            raise exceptions.NoDataError(
                f"Entsoe-client has no geneneration data found for {year, country}: {e}"
            )
    return pd.concat(d.values(), sort=True)


def _get_timestamps_for_month(year, tz, month):
    start = pd.Timestamp(year=year, month=month, day=1, tz=tz)
    _year = year if month < 12 else year + 1
    _month = month + 1 if month < 12 else 1
    end = pd.Timestamp(year=_year, month=_month, day=1, tz=tz)
    return start, end


def prep_residual_load(
    year: int = 2019, freq: str = "15min", country: str = "DE", method: str = "all_conv"
) -> pd.Series:
    config = dict(year=year, freq=freq, country=country)

    if method == "all_conv":
        return get_conventional_generation(**config)

    elif method == "conv2":
        return get_conv2_generation(**config)

    # elif method == "complex":
    #     load = load_el_national_load(**config).fillna(0)
    #     imports = load_imports(**config).sum(1).fillna(0)
    #     exports = load_exports(**config).sum(1).fillna(0)
    #     res_ser = get_renewable_generation(**config).fillna(0)
    #     return load - imports + exports - res_ser

    else:
        raise ValueError(f"Method {method} not implemented.")


def get_subset_of(df, subset: Union[List, Set]) -> Tuple[pd.Series, Set]:
    wanted = set(subset)
    available = wanted.intersection(set(df.keys()))
    return df[list(available)].sum(axis=1), available


def get_conventional_generation(year, freq, country) -> pd.Series:
    gen_TF = load_el_national_generation(year=year, freq=freq, country=country)
    conv_ser, available_conv = get_subset_of(gen_TF, mp.CONV)
    logger.info(f"Available CONV-fuels for {country}: {available_conv}")
    return conv_ser


def get_conv2_generation(year, freq, country) -> pd.Series:
    gen_TF = load_el_national_generation(year=year, freq=freq, country=country)
    conv_ser, available_conv = get_subset_of(gen_TF, mp.CONV2)
    logger.info(f"Available CONV-fuels for {country}: {available_conv}")
    return conv_ser


def get_renewable_generation(year, freq, country) -> pd.Series:
    gen_TF = load_el_national_generation(year=year, freq=freq, country=country)
    res_ser, available_vres = get_subset_of(gen_TF, mp.RES)
    logger.info(f"Available RES-fuels for {country}: {available_vres}")
    return res_ser


def load_el_national_specific_emissions() -> pd.DataFrame:
    """Read specific emissions data from [Tranberg.2019] in gCO2eq/kWh.

    [Tranberg.2019]: https://doi.org/10.1016/j.esr.2019.100367
    """
    fp = paths.DATA_DIR / f"tranberg/specific_emission_factors.csv"
    df = pd.read_csv(fp, header=0, index_col=0, skiprows=3).T
    return pd.DataFrame(
        {
            "wind_offshore": df["wind"],
            "wind_onshore": df["wind"],
            "nuclear": df["nuclear"],
            "other_RES": df["geothermal"],
            "biomass": df["biomass_cogeneration"],
            "pumped_hydro": df["hydropower_pumped_storage"],
            "hydro": df["hydropower_run-of-river"],
            "lignite": df["coal"],
            "other_conv": df["coal"],
            "coal": df["coal"],
            "gas": df["gas"],
            "oil": df["oil"],
            "solar": df["solar"],
        },
        index=df.index,
    ).T


def prep_shares(year: int = 2019, freq: str = "60min", country: str = "DE") -> pd.DataFrame:
    """Prepare shares of electricity production"""
    assert year in range(2000, 2100), f"{year} is not a valid year"
    assert freq in ["15min", "60min"], f"{freq} is not a valid freq"
    assert country in mp.EUROPE_COUNTRIES

    gen_TF = load_el_national_generation(year, country, freq="15min")
    gen_freq = hp.estimate_freq(gen_TF)

    gen_sums_T = gen_TF.sum(axis=1)
    shares_TF = gen_TF.copy()
    for f in shares_TF:
        shares_TF[f] = shares_TF[f] / gen_sums_T

    return hp.resample(shares_TF, year=year, start_freq=gen_freq, target_freq=freq)


def prep_dayahead_prices(
    year: int = 2019,
    freq: str = "60min",
    country: str = "DE",
    cache: bool = True,
    ensure_std_index: bool = True,
    fillna: bool = True,
    fill_outlier: bool = True,
    drop_ducplicates: bool = True,
    resample: bool = True,
) -> pd.Series:
    assert year in range(2000, 2100), f"{year} is not a valid year"
    assert country in entsoe.Area.__dict__

    fp = paths.CACHE_DIR / f"{year}_{freq}_{country}_dayahead_c_el_entsoe.parquet"

    # bidding_zone = get_bidding_zone(country, year)

    if cache and fp.exists():
        ser = hp.read(fp)

    else:
        ser = _query_day_ahead_prices(year, country)

        if cache:
            hp.write(ser, fp)

    if drop_ducplicates:
        ser = ser.groupby(ser.index).first()

    if ensure_std_index:
        idx = hp.make_datetimeindex(year, hp.estimate_freq(ser), tz=ser.index.tz)
        ser = ser.reindex(idx).ffill().bfill()
        ser = ser.reset_index(drop=True)

    if fillna:
        ser = ser.fillna(ser.mean())

    if fill_outlier:
        ser = hp.fill_outlier_and_nan(ser, zscore_threshold=50)

    if resample:
        ser = hp.resample(ser, year=year, start_freq=hp.estimate_freq(ser), target_freq=freq)

    hp.warn_if_incorrect_index_length(ser, year, freq)
    return ser


def _query_day_ahead_prices(year, bidding_zone) -> pd.Series:
    client = _get_client()
    tz = get_timezone(bidding_zone)
    try:
        start, end = _get_timestamps(year=year, tz=tz)
        ser = client.query_day_ahead_prices(start=start, end=end, country_code=bidding_zone)
    except entsoe.exceptions.NoMatchingDataError as e:
        raise exceptions.NoDataError(
            f"Entsoe-client has no price-data found for {year, bidding_zone}: {e}"
        )
    return ser


def get_bidding_zone(country: str, year: int) -> str:
    if year == 2018 and country == "IE":
        logger.warning(
            "Ireland coupled with GB on 2018-10-01 and changed from 30min to 60min Day-Ahead-Markt"
            " prices. See https://www.nordpoolgroup.com/message-center-container/newsroom/feature/2018/10/nord-pool-welcomes-power-coupling-with-ireland/"
        )
    if year <= 2018 and country == "AT":
        country = "DE"
        logger.info("AT and DE have the same prices.")

    if country in ["DE", "LU"]:
        if year > 2018:
            country = "DE-LU"
        else:
            country = "DE-AT-LU"

    country_to_bidding = {"NO": "NO-1", "DK": "DK-2", "IT": "IT-NORD", "SE": "SE-1", "IE": "IE-SEM"}
    return country_to_bidding.get(country, country)


def get_timezone(country: str) -> str:
    return entsoe.mappings.lookup_area(country).tz


#############################
# CURRENTLY UNUSED FUNCTIONS
#############################

# def load_imports(
#     year: int = 2019,
#     country: str = "DE",
#     freq: Optional[str] = "15min",
#     cache: bool = True,
#     ensure_std_index: bool = True,
# ) -> pd.DataFrame:

#     # see visualization of the ENTSO-E data under: https://www.energy-charts.de/exchange.htm

#     assert year in range(2000, 2100), f"{year} is not a valid year"
#     assert freq in [None, "15min", "30min", "60min"], f"{freq} is not a valid frequency"

#     aggregations = {
#         "DK": ["DK-1", "DK-2"],
#         "NO": ["NO-1", "NO-2", "NO-3", "NO-4", "NO-5"],
#         "SE": ["SE-1", "SE-2", "SE-3", "SE-4"],
#     }

#     if country in aggregations:
#         config = dict(year=year, freq=freq, ensure_std_index=ensure_std_index)
#         return sum([load_imports(country=region, **config) for region in aggregations[country]])

#     fp = paths.CACHE_DIR / f"{year}_{country}_import_entsoe.h5"

#     bidding_zone = get_bidding_zone(country=country, year=year)

#     if cache and fp.exists():
#         df = pd.read_hdf(fp)

#     else:
#         client = _get_client()
#         tz = get_timezone(bidding_zone)
#         start, end = _get_timestamps(year=year, tz=tz)
#         df = client.query_import(start=start, end=end, country_code=bidding_zone)
#         if cache:
#             hp.write(df, fp)

#     if ensure_std_index:
#         idx = hp.make_datetimeindex(year, hp.estimate_freq(df), tz=df.index.tz)
#         df = df.reindex(idx).fillna(method="ffill").fillna(method="bfill")

#     df = hp.resample(df, year=year, start_freq=hp.estimate_freq(df), target_freq=freq)

#     return df


# def load_crossborder_flows(
#     country_from: str,
#     country_to: str,
#     year: int = 2019,
#     #    freq: Optional[str] = "15min",
#     cache: bool = True,
#     #    ensure_std_index: bool = True
# ) -> pd.DataFrame:

#     assert year in range(2000, 2100), f"{year} is not a valid year"
#     # assert freq in [None, "15min", "30min", "60min"], f"{freq} is not a valid frequency"

#     fp = paths.CACHE_DIR / f"{year}_crossborder_{country_from}--{country_to}_entsoe.h5"

#     if cache and fp.exists():
#         ser = pd.read_hdf(fp)

#     else:
#         client = _get_client()
#         tz = get_timezone(get_bidding_zone(country=country_from, year=year))
#         start, end = _get_timestamps(year=year, tz=tz)

#         ser = client.query_crossborder_flows(country_from, country_to, start=start, end=end)
#         if cache:
#             hp.write(ser, fp)

#     # if ensure_std_index:
#     #     idx = hp.make_datetimeindex(year, hp.estimate_freq(ser), tz=ser.index.tz)
#     #     ser = ser.reindex(idx).fillna(method="ffill").fillna(method="bfill")

#     # ser = hp.resample(ser, year=year, start_freq=hp.estimate_freq(ser), target_freq=freq)

#     return ser


# def load_exports(
#     year: int = 2019,
#     country: str = "DE",
#     freq: Optional[str] = "15min",
#     cache: bool = True,
#     ensure_std_index: bool = True,
# ) -> pd.DataFrame:

#     assert year in range(2000, 2100), f"{year} is not a valid year"
#     assert freq in [None, "15min", "30min", "60min"], f"{freq} is not a valid frequency"

#     fp = paths.CACHE_DIR / f"{year}_{country}_export_entsoe.h5"

#     bzone_from = get_bidding_zone(country=country, year=year)

#     if cache and fp.exists():
#         df = pd.read_hdf(fp)

#     else:
#         client = _get_client()
#         export_dic = {}
#         for bzone_to in entsoe_mp.NEIGHBOURS[bzone_from]:
#             tz = get_timezone(country=bzone_to)
#             start, end = _get_timestamps(year=year, tz=tz)
#             try:
#                 export_dic[bzone_to] = client.query_crossborder_flows(
#                     country_code_from=bzone_from,
#                     country_code_to=bzone_to,
#                     start=start,
#                     end=end,
#                     lookup_bzones=True,
#                 )
#             except entsoe.exceptions.NoMatchingDataError:
#                 logger.warning(f"NoMatchingDataError: No data for export to {bzone_to}")

#         df = pd.concat(export_dic, axis=1)
#         if cache:
#             hp.write(df, fp)

#     if ensure_std_index:
#         idx = hp.make_datetimeindex(year, hp.estimate_freq(df), tz=df.index.tz)
#         df = df.reindex(idx).fillna(method="ffill").fillna(method="bfill")

#     df = hp.resample(df, year=year, start_freq=hp.estimate_freq(df), target_freq=freq)

#     return df


# def load_el_national_load(
#     year: int = 2019,
#     freq: str = "15min",
#     country: str = "DE",
#     cache: bool = True,
#     ensure_std_index: bool = True,
#     resample: bool = True,
# ) -> pd.Series:
#     assert year in range(2000, 2100), f"{year} is not a valid year"
#     assert freq in [None, "15min", "30min", "60min"], f"{freq} is not a valid freq"
#     assert country in mp.EUROPE_COUNTRIES or country in entsoe_mp.BIDDING_ZONES

#     fp = paths.CACHE_DIR / f"{year}_{country}_load_entsoe.h5"

#     if cache and fp.exists():
#         ser = pd.read_hdf(fp)

#     else:
#         if country == "DE" and year == 2018:
#             a = load_el_national_load(year=year, freq=freq, country="DE-AT-LU")
#             b = load_el_national_load(year=year, freq=freq, country="DE-LU")
#             idx = hp.make_datetimeindex(year=year, freq=freq, tz=a.index.tz)
#             ser = pd.concat([a, b], axis=1).mean(1)

#         else:
#             client = _get_client()
#             tz = get_timezone(country)
#             try:
#                 start, end = _get_timestamps(year=year, tz=tz)
#                 ser = client.query_load(start=start, end=end, country_code=country)
#             except entsoe.exceptions.NoMatchingDataError as e:
#                 raise exceptions.NoDataError(
#                     f"Entsoe-client has no load-data found for {year, country}: {e}"
#                 )

#         if cache:
#             hp.write(ser, fp)

#     if ensure_std_index:
#         idx = hp.make_datetimeindex(year, hp.estimate_freq(ser), tz=ser.index.tz)
#         ser = ser.reindex(idx).fillna(method="ffill").fillna(method="bfill").reset_index(drop=True)

#     if resample:
#         ser = hp.resample(ser, year=year, start_freq=hp.estimate_freq(ser), target_freq=freq)
#     return ser
