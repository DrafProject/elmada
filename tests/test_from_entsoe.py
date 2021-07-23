import numpy as np
import pandas as pd
import pytest
from entsoe import EntsoePandasClient

from elmada import exceptions, from_entsoe
from elmada import helper as hp
from elmada import mappings as mp
from elmada import paths

country_resi_means = [
    ("AT", 1791),
    ("BE", 8285),
    ("CZ", 8143),
    ("DE", 31805),
    ("DK", 764),
    ("ES", 17111),
    ("FI", 4181),
    ("FR", 49036),
    ("GB", 20016),
    ("GR", 3244),
    ("HU", 3157),
    ("IE", 1560),
    ("IT", 18920),
    ("LT", 131),
    ("NL", 9014),
    ("PL", 14572),
    ("PT", 2804),
    ("RO", 3934),
    ("RS", 2786),
    ("SI", 1154),
]


@pytest.mark.parametrize("country,mean", country_resi_means)
def test_prep_residual_load(country, mean):
    assert mean == pytest.approx(
        from_entsoe.prep_residual_load(year=2019, country=country).mean(), 0.01
    )


def test_prep_residual_load_with_conv2(mocker):
    mock = mocker.patch("elmada.from_entsoe.get_conv2_generation")
    from_entsoe.prep_residual_load(year=2019, country="DE", method="conv2")
    mock.assert_called_once()


def test_prep_residual_load_method_not_implemented():
    with pytest.raises(ValueError):
        from_entsoe.prep_residual_load(
            year=2019, country="DE", method="this_method_is_not_implemented"
        )


def test_prep_XEFs():
    result = from_entsoe.prep_XEFs(year=2019, freq="60min", country="DE")
    assert isinstance(result, pd.DataFrame)


@pytest.mark.apikey
def test_load_installed_generation_capacity():
    result = from_entsoe.load_installed_generation_capacity(year=2019, country="DE", cache=False)
    assert isinstance(result, pd.DataFrame)


def test_prep_dayahead_prices(mocker):
    dummy = pd.Series(30, index=range(8760))
    dummy[2] = np.nan
    dummy[5] = 5000.0
    dummy.index = hp.make_datetimeindex(year=2019, freq="60min", tz="Europe/Berlin")
    assert isinstance(dummy.index, pd.DatetimeIndex)

    mocker.patch("elmada.from_entsoe._query_day_ahead_prices", return_value=dummy)
    result = from_entsoe.prep_dayahead_prices(year=2019, freq="60min", country="DE", cache=False)

    assert isinstance(result, pd.Series)
    assert result[2] == 30
    assert result[5] == 30
    assert isinstance(result.index, pd.RangeIndex)


def test_get_empty_installed_generation_capacity_df():
    result = from_entsoe._get_empty_installed_generation_capacity_df(ensure_std_techs=True)
    expected = pd.DataFrame(index=mp.DRAF_FUELS, columns=[""]).T
    assert result.equals(expected)

    with pytest.raises(exceptions.NoDataError):
        from_entsoe._get_empty_installed_generation_capacity_df(ensure_std_techs=False)


def test_get_conv2_generation():
    result = from_entsoe.get_conv2_generation(year=2019, freq="60min", country="DE")
    assert isinstance(result, pd.Series)


def test_get_renewable_generation():
    result = from_entsoe.get_renewable_generation(year=2019, freq="60min", country="DE")
    assert isinstance(result, pd.Series)


@pytest.mark.apikey
def test_load_el_national_generation(mocker):
    df = hp.read(paths.SAFE_CACHE_DIR / "2019_DE_gen_entsoe.parquet")
    mock = mocker.patch("entsoe.EntsoePandasClient.query_generation", return_value=df)
    result = from_entsoe.load_el_national_generation(
        year=2019, country="DE", freq="15min", cache=False, split_queries=False
    )
    mock.assert_called()
    assert isinstance(result, pd.DataFrame)


def test_get_bidding_zone():
    assert from_entsoe.get_bidding_zone(country="AT", year=2017) == "DE-AT-LU"


def test_query_day_ahead_prices(mocker):
    mocker.patch("elmada.from_entsoe._get_client", return_value=EntsoePandasClient)
    mock = mocker.patch("entsoe.EntsoePandasClient.query_day_ahead_prices")
    from_entsoe._query_day_ahead_prices(
        2019, bidding_zone=from_entsoe.get_bidding_zone(country="DE", year=2019)
    )
    mock.assert_called_once()


def test__query_generation(mocker):
    mocker.patch("elmada.from_entsoe._get_client", return_value=EntsoePandasClient)
    mock = mocker.patch("entsoe.EntsoePandasClient.query_generation", return_value=pd.DataFrame())
    from_entsoe._query_generation(year=2019, country="DE", split_queries=False)
    mock.assert_called_once()

    mock = mocker.patch("entsoe.EntsoePandasClient.query_generation", return_value=pd.DataFrame())
    from_entsoe._query_generation(year=2019, country="DE", split_queries=True)
    assert mock.call_count == 12
