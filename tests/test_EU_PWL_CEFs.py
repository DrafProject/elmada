import pandas as pd
import pytest
from elmada import el_EU_PWL_CEFs as pwl


def test_prep_prices(mocker):
    mock = mocker.patch("elmada.el_EU_PWL_CEFs.prep_CEFs", return_value={"marginal_cost": 42})
    result = pwl.prep_prices(year=2019, freq="60min", country="DE")
    assert result == 42
    mock.assert_called_once_with(year=2019, freq="60min", country="DE")


def test_prep_CEFs(mocker):
    mock = mocker.patch("elmada.el_opsd.get_CEFs_from_merit_order")
    pwl.prep_CEFs(year=2019, freq="60min", country="DE")
    mock.assert_called_once()


def test_approximate_min_max_values_raises_error():
    result = pwl.approximate_min_max_values(method="interp")
    assert isinstance(result, tuple)

    with pytest.raises(ValueError):
        pwl.approximate_min_max_values(method="this_method_is_not_implemented")


def test_prep_installed_generation_capacity():
    with pytest.raises(ValueError):
        pwl.prep_installed_generation_capacity(source="this_method_is_not_implemented")


def test_get_pp_size():
    with pytest.raises(ValueError):
        pwl.get_pp_size(pp_size_method="this_method_is_not_implemented", country="DE", fuel="gas")


def test_get_pp_sizes_from_germany():
    result = pwl.get_pp_sizes_from_germany()
    assert isinstance(result, pd.Series)
