from typing import Dict

import pandas as pd
import pytest

from elmada import from_other


def test_get_transmission_efficiency_series():
    assert isinstance(from_other.get_transmission_efficiency_series(cache=True), pd.Series)
    assert isinstance(from_other.get_transmission_efficiency_series(cache=False), pd.Series)


def test_get_transmission_efficiency():
    result = from_other.get_transmission_efficiency("THIS_IS_NOT_A_VALID_COUNTRY")
    assert isinstance(result, float)


def test__get_light_oil_conversion_factor():
    assert from_other._get_light_oil_conversion_factor(source=1) == 0.980


def test_get_ice_eua_prices_with_cache():
    result = from_other.get_ice_eua_prices(cache=True)
    assert isinstance(result, Dict)


@pytest.mark.apikey
def test_get_ice_eua_prices_without_cache():
    result = from_other.get_ice_eua_prices(cache=False)
    assert isinstance(result, Dict)


def test_get_sandbag_eua_prices():
    result = from_other.get_sandbag_eua_prices()
    assert isinstance(result, Dict)
