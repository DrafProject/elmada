import pandas as pd
import pytest  # pylint: disable=unused-import

from elmada import el_opsd as od
from elmada import helper as hp
import elmada


def test_prep_CEFs():
    cefs = od.prep_CEFs(year=2019, freq="60min", country="DE")

    target = pd.Index(
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
    assert cefs.keys().equals(target)

    assert hp.is_correct_length(cefs, year=2019, freq="60min")

    assert isinstance(cefs, pd.DataFrame)


def test_read_opsd_powerplant_list():
    tmp_mode = elmada.get_mode()

    elmada.set_mode("safe")
    df = od.read_opsd_powerplant_list()
    assert len(df) == 893

    elmada.set_mode("live")
    df = od.read_opsd_powerplant_list()
    assert len(df) != 893

    elmada.set_mode(tmp_mode)

