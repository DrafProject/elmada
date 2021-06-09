import pandas as pd
import pytest
from elmada import el_entsoepy as ep
from elmada import exceptions
from elmada import helper as hp
from elmada import mappings as mp
from elmada import paths
from entsoe import EntsoePandasClient

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
    assert mean == pytest.approx(ep.prep_residual_load(year=2019, country=country).mean(), 0.01)


def test_prep_residual_load_with_conv2(mocker):
    mock = mocker.patch("elmada.el_entsoepy.get_conv2_generation")
    ep.prep_residual_load(year=2019, country="DE", method="conv2")
    mock.assert_called_once()


def test_prep_residual_load_method_not_implemented():
    with pytest.raises(ValueError):
        ep.prep_residual_load(year=2019, country="DE", method="this_method_is_not_implemented")


def test_prep_XEFs():
    result = ep.prep_XEFs(year=2019, freq="60min", country="DE")
    assert isinstance(result, pd.DataFrame)


@pytest.mark.apikey
def test_load_installed_generation_capacity():
    result = ep.load_installed_generation_capacity(year=2019, country="DE", cache=False)
    assert isinstance(result, pd.DataFrame)


@pytest.mark.apikey
def test_prep_dayahead_prices():
    ep.prep_dayahead_prices(year=2019, freq="60min", country="DE")


def test_get_empty_installed_generation_capacity_df():
    result = ep._get_empty_installed_generation_capacity_df(ensure_std_techs=True)
    expected = pd.DataFrame(index=mp.DRAF_FUELS, columns=[""]).T
    assert result.equals(expected)

    with pytest.raises(exceptions.NoDataError):
        ep._get_empty_installed_generation_capacity_df(ensure_std_techs=False)


def test_get_conv2_generation():
    result = ep.get_conv2_generation(year=2019, freq="60min", country="DE")
    assert isinstance(result, pd.Series)


def test_get_renewable_generation():
    result = ep.get_renewable_generation(year=2019, freq="60min", country="DE")
    assert isinstance(result, pd.Series)


@pytest.mark.apikey
def test_load_el_national_generation(mocker):
    df = hp.read(paths.SAFE_CACHE_DIR / "2019_DE_gen_entsoe.parquet")
    mock = mocker.patch("entsoe.EntsoePandasClient.query_generation", return_value=df)
    result = ep.load_el_national_generation(
        year=2019, country="DE", freq="15min", cache=False, split_queries=False
    )
    mock.assert_called()
    assert isinstance(result, pd.DataFrame)


def test_query_day_ahead_prices(mocker):
    mocker.patch("elmada.el_entsoepy._get_client", return_value=EntsoePandasClient)
    mock = mocker.patch("entsoe.EntsoePandasClient.query_day_ahead_prices")
    ep._query_day_ahead_prices(2019, bidding_zone=ep.get_bidding_zone(country="DE", year=2019))
    mock.assert_called_once()


def test__query_generation(mocker):
    mocker.patch("elmada.el_entsoepy._get_client", return_value=EntsoePandasClient)
    mock = mocker.patch("entsoe.EntsoePandasClient.query_generation", return_value=pd.DataFrame())
    ep._query_generation(year=2019, country="DE", split_queries=False)
    mock.assert_called_once()

    mock = mocker.patch("entsoe.EntsoePandasClient.query_generation", return_value=pd.DataFrame())
    ep._query_generation(year=2019, country="DE", split_queries=True)
    assert mock.call_count == 12
