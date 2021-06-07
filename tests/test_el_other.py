from typing import Dict
import pandas as pd
from elmada import el_other as ot
import pytest


def test_get_transmission_efficiency_series():
    assert isinstance(ot.get_transmission_efficiency_series(cache=True), pd.Series)
    assert isinstance(ot.get_transmission_efficiency_series(cache=False), pd.Series)


def test_get_transmission_efficiency():
    result = ot.get_transmission_efficiency("THIS_IS_NOT_A_VALID_COUNTRY")
    assert isinstance(result, float)


def test__get_light_oil_conversion_factor():
    assert ot._get_light_oil_conversion_factor(source=1) == 0.980


def test_get_ice_eua_prices_with_cache():
    result = ot.get_ice_eua_prices(cache=True)
    assert isinstance(result, Dict)


@pytest.mark.slow
def test_get_ice_eua_prices_without_cache():
    result = ot.get_ice_eua_prices(cache=False)
    assert isinstance(result, Dict)
