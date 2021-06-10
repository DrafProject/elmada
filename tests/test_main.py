import elmada
import pandas as pd
import pytest


def test_get_emissions(mocker):
    config = dict(year=2019, freq="60min", country="DE")

    methodtuples = [
        ("_EP", "elmada.from_entsoe.prep_XEFs", config),
        ("_PP", "elmada.from_opsd.prep_CEFs", config),
        ("_PWL", "elmada.eu_pwl.prep_CEFs", dict(**config, validation_mode=False)),
        ("_PWLv", "elmada.eu_pwl.prep_CEFs", dict(**config, validation_mode=True)),
    ]

    for (method, func, kwargs) in methodtuples:
        print(method, func, kwargs)
        mock = mocker.patch(func)
        elmada.get_emissions(**config, cache=False, method=method)
        mock.assert_called_once_with(**kwargs)


pp_keys = pd.Index(
    [
        "id",
        "name_bnetza",
        "block_bnetza",
        "name_uba",
        "company",
        "street",
        "postcode",
        "city",
        "state",
        "country_code",
        "capa",
        "capacity_gross_uba",
        "fuel",
        "technology",
        "chp",
        "chp_capacity_uba",
        "commissioned",
        "commissioned_original",
        "retrofit",
        "shutdown",
        "status",
        "type",
        "lat",
        "lon",
        "eic_code_plant",
        "eic_code_block",
        "efficiency_data",
        "efficiency_source",
        "efficiency_estimate",
        "energy_source_level_1",
        "energy_source_level_2",
        "energy_source_level_3",
        "eeg",
        "network_node",
        "voltage",
        "network_operator",
        "merge_comment",
        "comment",
        "fuel_draf",
        "filler",
        "eta_k",
        "used_eff",
        "marginal_emissions_for_gen",
        "x_k",
        "fuel_cost",
        "GHG_cost",
        "marginal_emissions",
        "marginal_cost",
        "cumsum_capa",
    ],
    dtype="object",
)

pwl_keys = pd.Index(
    [
        "capa",
        "used_eff",
        "fuel_draf",
        "x_k",
        "fuel_cost",
        "GHG_cost",
        "marginal_emissions",
        "marginal_cost",
        "cumsum_capa",
    ],
    dtype="object",
)


@pytest.mark.parametrize(
    "method,expected_keys", [("PP", pp_keys), ("PWL", pwl_keys), ("PWLv", pwl_keys)]
)
def test_get_merit_order(method, expected_keys):
    df = elmada.get_merit_order(year=2019, country="DE", method=method)
    assert isinstance(df, pd.DataFrame)
    df.keys().equals(expected_keys)


def test_get_residual_load(mocker):
    config = dict(year=2019, freq="60min", country="DE")
    mock = mocker.patch("elmada.from_entsoe.prep_residual_load", return_value=True)
    assert elmada.from_entsoe.prep_residual_load(**config)
    mock.assert_called_once_with(**config)


def test_get_prices(mocker):
    config = dict(year=2019, freq="60min", country="DE", cache=True)
    ep_mock = mocker.patch("elmada.from_entsoe.prep_dayahead_prices", return_value=True)
    assert elmada.get_prices(**config, method="hist_EP")
    ep_mock.assert_called_once_with(**config)

    sm_mock = mocker.patch("elmada.from_smard.prep_dayahead_prices", return_value=True)
    assert elmada.get_prices(**config, method="hist_SM")
    sm_mock.assert_called_once_with(**config)

    pp_mock = mocker.patch("elmada.main.get_emissions", return_value={"marginal_cost": True})
    elmada.get_prices(**config, method="PP")
    pp_mock.assert_called_once_with(**config, method="_PP")

    pwl_mock = mocker.patch("elmada.main.get_emissions", return_value={"marginal_cost": True})
    elmada.get_prices(**config, method="PWL")
    pwl_mock.assert_called_once_with(**config, method="_PWL")
