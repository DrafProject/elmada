import pandas as pd
import pytest

from elmada import eu_pwl


def test_prep_prices(mocker):
    mock = mocker.patch("elmada.eu_pwl.prep_CEFs", return_value={"marginal_cost": 42})
    result = eu_pwl.prep_prices(year=2019, freq="60min", country="DE")
    assert result == 42
    mock.assert_called_once_with(year=2019, freq="60min", country="DE")


@pytest.mark.wantcache
def test_prep_CEFs(mocker):
    mock = mocker.patch("elmada.from_opsd.get_CEFs_from_merit_order")
    eu_pwl.prep_CEFs(year=2019, freq="60min", country="DE")
    mock.assert_called_once()


def test_approximate_min_max_values_raises_error():
    result = eu_pwl.approximate_min_max_values(method="interp")
    assert isinstance(result, tuple)

    with pytest.raises(ValueError):
        eu_pwl.approximate_min_max_values(method="this_method_is_not_implemented")


def test_prep_installed_generation_capacity():
    with pytest.raises(ValueError):
        eu_pwl.prep_installed_generation_capacity(source="this_method_is_not_implemented")


def test_get_pp_size():
    with pytest.raises(ValueError):
        eu_pwl.get_pp_size(
            pp_size_method="this_method_is_not_implemented", country="DE", fuel="gas"
        )


def test_get_pp_sizes_from_germany():
    result = eu_pwl.get_pp_sizes_from_germany()
    assert isinstance(result, pd.Series)
