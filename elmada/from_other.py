import logging
from io import StringIO
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from elmada import get_mode
from elmada import helper as hp
from elmada import mappings as mp
from elmada import paths

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARN)


def get_ETS_price(year: int) -> float:
    prices = get_ETS_prices()
    try:
        return prices[year]
    except KeyError:
        max(prices.keys())
        backup_value = prices[max(prices.keys())]
        logger.warning(
            f"No data for ETS price for {year} "
            f"==> Default value of latest available year with {backup_value:.2f} €/t is given."
        )
        return backup_value


def get_ETS_prices() -> Dict:
    """Returns carbon emission prices of the EU emissions trading system (ETS) for different years.

    Source:
        * EEX (https://www.eex.com/en/market-data/environmental-markets/auction-market/european-emission-allowances-auction)
        via Sandbag (https://sandbag.org.uk/carbon-price-viewer/)
        * ICE via Quandl
    """
    mode = get_mode()
    if mode == "live":
        return get_ice_eua_prices()

    elif mode == "safe":
        return get_sandbag_eua_prices()
    else:
        raise RuntimeError()


def get_ice_eua_prices(cache: bool = True) -> Dict:
    """Get EUA prices from ICE [1] via Quandl [2].

    Sources:
        [1] https://www.theice.com/
        [2] https://www.quandl.com/data/CHRIS/ICE_C1-ECX-EUA-Futures-Continuous-Contract-1-C1-Front-Month
    """
    fp = paths.mode_dependent_cache_dir() / "QUANDL_eua_prices.parquet"

    if cache and fp.exists():
        ser = hp.read(fp)
    else:
        import quandl

        quandl.ApiConfig.api_key = hp.get_api_key("quandl")
        df = quandl.get("CHRIS/ICE_C1")
        ser = df["Settle"].resample("y").mean().rename("Price")
        ser.index = ser.index.year
        if cache:
            hp.write(ser, fp)

    return ser.to_dict()


def get_sandbag_eua_prices() -> Dict:
    """Get ETS EUA prices via Sandbag"""
    fp = paths.DATA_DIR / "sandbag/eua-price.csv"

    # # fix bad csv-syntax
    s = fp.read_text(encoding="utf8").replace('",', '";')

    io = StringIO(s)
    df = pd.read_csv(io, sep=";", decimal=",", index_col=0, skiprows=2)

    df.index = pd.to_datetime(df.index)
    df = df.resample("Y").mean()
    df = df.set_index(df.index.year, drop=True)
    return df.squeeze().to_dict()


def _get_light_oil_conversion_factor(source: int = 2):
    """Get the calorific value for light oil in MWh/Hektoliter from different sources.

    Sources:
    [1]: Heizöl Total (https://www.heizoel.total.de/rund-um-heizoel/aktuelles-tipps/heizoelkauf-beratung/heizwert-und-brennwert-von-heizol/)
        raw value: 9.8 kWh/l

    [2]: Mineralöl Franken (https://www.mineraloel-franken.de/fileadmin/redaktion/downloads/Produktspezifikation_Heizoel_EL_Total.pdf)
        raw values: 42.6 MJ/kg for light oil with a density of 860 kg/m³.
    """
    if source == 1:
        return 0.980

    if source == 2:
        return (
            42.6  # MJ/kg
            * 860  # kg/m³ ==> MJ/m³
            / 3600  # MJ/MWh ==> MWh/m³
            / 10  # Hektoliter/m³ ==> MWh/Hektoliter
        )


def _get_light_oil_price(year: int = 2019):
    """Get light oil price in €/MWh.

    Source: StatistischeBundesamt.2020 (https://www.destatis.de/DE/Themen/Wirtschaft/Preise/Publikationen/Energiepreise/energiepreisentwicklung-pdf-5619001.html)
    """
    data = pd.Series(
        {
            2005: 42.42,
            2006: 47.58,
            2007: 46.83,
            2008: 61.76,
            2009: 40.81,
            2010: 52.31,
            2011: 66.51,
            2012: 72.94,
            2013: 67.96,
            2014: 61.88,
            2015: 46.19,
            2016: 38.40,
            2017: 45.05,
            2018: 55.27,
            2019: 53.69,
        }
    )
    return (
        data[year] / _get_light_oil_conversion_factor()  # €/Hektoliter  # MWh/Hektoliter ==> €/MWh
    )


def _get_lignite_price(year: int = 2019, base_price: float = 6.3) -> float:
    """Get lignite price in €/MWh. Calculated as product of a destatis index and an baseprice for
    the year 2015.

    Source:
        indices: StatistischeBundesamt.2020 (https://www.destatis.de/DE/Themen/Wirtschaft/Preise/Publikationen/Energiepreise/energiepreisentwicklung-pdf-5619001.html)
        base_price: Konstantin.2017 (https://doi.org/10.1007/978-3-662-49823-1)
    """
    fp = paths.DATA_DIR / "destatis/energiepreisentwicklung-xlsx-5619001.xls"
    xl = pd.ExcelFile(fp)
    df = xl.parse(
        sheet_name=7, skiprows=28, header=None, skipfooter=0, index_col=0, na_values="-"
    ).dropna(axis=0, how="all")[13]

    df.index = df.index.str.slice(0, 5).astype(int)
    return df[year] * base_price / 100


def _get_coal_price(year: int = 2019, base_price: float = 10.12) -> float:
    """Get coal price in €/MWh. Calculated as product of a destatis index and an baseprice for
    the year 2015.

    Source:
        indices: StatistischeBundesamt.2020 (https://www.destatis.de/DE/Themen/Wirtschaft/Preise/Publikationen/Energiepreise/energiepreisentwicklung-pdf-5619001.html)
        base_price: Konstantin.2017 (https://doi.org/10.1007/978-3-662-49823-1)
    """
    fp = paths.DATA_DIR / "destatis/energiepreisentwicklung-xlsx-5619001.xls"
    xl = pd.ExcelFile(fp)
    df = xl.parse(
        sheet_name=7, skiprows=7, header=None, skipfooter=21, index_col=0, na_values="-"
    ).dropna(axis=0, how="all")[13]

    df.index = df.index.str.slice(0, 5).astype(int)
    return df[year] * base_price / 100


def _get_gas_price(year: int = 2019, country: str = "DE") -> float:
    """Get gas price in €/MWh. including excise taxes, without value-added tax.
    Data for most European countries in the years 2008 - 2019.

    Source: StatistischeBundesamt.2020 (https://www.destatis.de/DE/Themen/Wirtschaft/Preise/Publikationen/Energiepreise/energiepreisentwicklung-pdf-5619001.html)
    """
    fp = paths.DATA_DIR / "destatis/energiepreisentwicklung-xlsx-5619001.xls"
    xl = pd.ExcelFile(fp)
    nblocks = 4
    blocksize = 26
    block_list = []
    for i in range(nblocks):
        block_list.append(
            xl.parse(
                sheet_name=11,
                skiprows=4 + i * blocksize,
                skipfooter=blocksize * (nblocks - 1 - i) + 2,
                index_col=0,
                na_values="-",
            ).dropna(axis=0, how="all")
        )
    df = pd.concat(block_list, sort=False, join="outer", axis=1).dropna(axis=1, how="all")
    df["year"] = df.index.str.slice(5).astype(int)
    df = df.groupby("year").mean()  # get mean between year-halfs

    df = df / 100 * 1000  # convert cent/kWh into €/MWh

    default_value = df.mean().mean()
    warn_msg = (
        f"No data for gas price for {year},{country} ==> "
        f"Default value {default_value:.2f} €/MWh is given."
    )
    try:
        price = df.loc[year, mp.EU_de_for_gas_price[country]]
    except KeyError:
        logger.warning(warn_msg)
        return default_value

    if np.isnan(price):
        logger.warning(warn_msg)
        return default_value

    else:
        return price


def get_fuel_prices(year: int = 2019, country: str = "DE") -> Dict:
    """Get x_k: Fuel price [€ / MWh]

    Source:
        Nuclear: Konstantin.2017 (https://doi.org/10.1007/978-3-662-49823-1)
        Rest:
            StatistischeBundesamt.2020 (https://www.destatis.de/DE/Themen/Wirtschaft/Preise/Publikationen/Energiepreise/energiepreisentwicklung-pdf-5619001.html)
            + Konstantin.2017 (https://doi.org/10.1007/978-3-662-49823-1)
    """
    gas_price = _get_gas_price(year=year, country=country)
    try:
        return dict(
            oil=_get_light_oil_price(year=year),
            gas_cc=gas_price,
            gas=gas_price,
            coal=_get_coal_price(year=year),
            lignite=_get_lignite_price(year=year),
            nuclear=4.18,
        )
    except KeyError:  # if values for future years are missing
        return get_fuel_prices(year=2019)


def get_baumgaertner_data() -> Dict:
    """Nomentclature

    Per Fuel-type k
        - x_k: Fuel price [€ / MWh]
        - mu_co2_k: Carbon emission intensity [t_CO2eq / t_k]
        - H_u_k: Calorific value [MWh / t_k]
        - eta_k: Efficiency [MWh_el / MWh]

    Source: Baumgärtner.2019 (https://doi.org/10.1016/j.apenergy.2019.04.029)
        fuel prices: Konstantin.2017 (https://doi.org/10.1007/978-3-662-49823-1)
    """
    return dict(
        x_k=dict(oil=38.63, gas_cc=26.71, gas=29.81, coal=10.12, lignite=6.3, nuclear=4.18),
        mu_co2_k=dict(oil=3.15, gas_cc=1.93, gas=1.93, coal=2.6, lignite=1.39, nuclear=0.0),
        H_u_k=dict(
            oil=42.6 / 3.6,
            gas_cc=38.27 / 3.6,
            gas=38.27 / 3.6,
            coal=26.47 / 3.6,
            lignite=14.99 / 3.6,
            nuclear=41667.0,
        ),
        eta_k=dict(oil=0.373, gas_cc=0.50, gas=0.349, coal=0.377, lignite=0.356, nuclear=0.32),
    )


def get_emissions_per_fuel_quaschning() -> Dict:
    """Carbon emissions per fuel type [t_CO2eq / MWh]

    Source: Quaschning.2015 (https://www.volker-quaschning.de/datserv/CO2-spez/index_e.php)"""
    return dict(oil=0.28, gas_cc=0.25, gas=0.25, coal=0.34, lignite=0.36, nuclear=0.0)


def prepare_transmission_losses() -> pd.DataFrame:
    """Source: WorldBank.2020 (https://databank.worldbank.org/reports.aspx?source=2&series=EG.ELC.LOSS.ZS)"""
    fp = paths.DATA_DIR / "worldbank/Data_Extract_From_World_Development_Indicators/Data.csv"
    df = pd.read_csv(fp, nrows=58, na_values="..", index_col=2).iloc[:, 3:]
    df = df.rename(columns={k: k[:4] for k in df.keys()})
    df["mean"] = df.loc[:, "2010":"2014"].mean(1)
    return df


def get_transmission_efficiency_series(fillna: bool = True, cache: bool = True) -> pd.Series:
    """Returns a Series with transmission efficiencies and long country names in index."""

    fp = paths.mode_dependent_cache_dir() / "transmission_efficiencies.parquet"

    if cache and fp.exists():
        ser = hp.read(fp)

    else:
        df = prepare_transmission_losses()
        ser = df["mean"]
        if cache:
            hp.write(ser, fp)

    if fillna:
        na_countries = list(ser[ser.isna()].index)
        filler = ser.mean()
        ser = ser.fillna(filler)
        logger.info(f"No data for transmission efficiency for {na_countries}")

    return 1 - (ser / 100)


def get_transmission_efficiency(country: str) -> float:
    """Returns scalar value of transmission efficiency."""
    ser = get_transmission_efficiency_series()

    try:
        cy_long = mp.EUROPE_COUNTRIES[country]
        return ser[cy_long]

    except KeyError:
        default = ser.mean()
        logger.warning(
            f"No transmission efficiency data for {country}. European mean of {default} given."
        )
        return default
