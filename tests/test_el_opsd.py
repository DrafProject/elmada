import elmada
import pandas as pd
from elmada import el_opsd as od
from elmada import helper as hp
from elmada.mode import ConfigUtil
from pytest_mock import MockerFixture


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
    mocker.patch.object(ConfigUtil, "mode", "safe")
    assert elmada.get_mode() == "safe"
    assert len(od.read_opsd_powerplant_list()) == 893

    mocker.patch.object(ConfigUtil, "mode", "live")
    assert elmada.get_mode() == "live"
    assert len(od.read_opsd_powerplant_list()) != 893
