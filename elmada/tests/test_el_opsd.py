import pandas as pd
import pytest  # pylint: disable=unused-import

import draf
import elmada
from elmada import helper as hp
from elmada import el_opsd as od


@pytest.fixture
def merit_order():
    return elmada.get_merit_order(year=2019, method="PWL")


def test_get_CEFs_from_merit_oder(merit_order):
    mo_P = merit_order
    max_merit_order = mo_P[mo_P.fuel_draf == "lignite"].cumsum_capa.max()
    cefs = od.get_CEFs_from_merit_order(mo_P=mo_P, year=2019, freq="60min", country="DE")
    cefs
    max_cefs = cefs[cefs.marginal_fuel == "lignite"].residual_load.max()
    assert max_cefs < max_merit_order
    assert isinstance(cefs, pd.DataFrame)


def test_prep_prices():
    ser = od.prep_prices()
    assert isinstance(ser, pd.Series)


def test_prep_CEFs(merit_order):
    year = 2019
    freq = "60min"
    for mo_P in [None, merit_order]:
        cefs = od.prep_CEFs(year=year, freq=freq, country="DE", mo_P=mo_P)

        a = set(cefs.keys())
        b = set(
            [
                "residual_load",
                "total_load",
                "marginal_fuel",
                "efficiency",
                "marginal_cost",
                "MEFs",
                "XEFs",
            ]
        )
        assert a == b

        assert hp.is_correct_length(cefs, year=year, freq=freq)

        assert isinstance(cefs, pd.DataFrame)
