import elmada
import pandas as pd
from elmada import el_opsd as od
from elmada import helper as hp
from elmada.mode import ConfigUtil
from pytest_mock import MockerFixture
from elmada import paths


def test_prep_prices(mocker):
    mock = mocker.patch("elmada.el_opsd.prep_CEFs", return_value={"marginal_cost": 42})
    assert od.prep_prices(year=2019, freq="60min", country="DE") == 42
    mock.assert_called_once_with(year=2019, freq="60min", country="DE")


def test_prep_CEFs():
    cefs = od.prep_CEFs(year=2019, freq="60min", country="DE")

    expected = pd.Index(
        data=[
            "residual_load",
            "total_load",
            "marginal_fuel",
            "efficiency",
            "marginal_cost",
            "MEFs",
            "XEFs",
        ],
        dtype="object",
    )
    assert cefs.keys().equals(expected)

    assert hp.is_correct_length(cefs, year=2019, freq="60min")

    assert isinstance(cefs, pd.DataFrame)


def test_read_opsd_powerplant_list(mocker: MockerFixture):
    for mode in ["safe", "live"]:

        mocker.patch.object(ConfigUtil, "mode", mode)
        assert elmada.get_mode() == mode
        df = od.read_opsd_powerplant_list()
        if mode == "safe":
            assert len(df) == 893
        else:
            assert len(df) != 893
        assert "fuel" in df


def test_get_summary():
    result = od.get_summary()
    assert isinstance(result, pd.DataFrame)


def test_get_summary_of_opsd_raw():
    result = od.get_summary_of_opsd_raw()
    assert isinstance(result, pd.DataFrame)


def test_download_powerplant_list(mocker):
    mock = mocker.patch("requests.get")
    type(mock.return_value).content = mocker.PropertyMock(return_value="xx".encode())
    fp = paths.CACHE_DIR / "test_file.csv"
    od.download_powerplant_list(which="DE", fp=fp)
    assert fp.exists()
    fp.unlink()
    mock.assert_called_once()
