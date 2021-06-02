import elmada
import pandas as pd
import pytest

from .common import hasher


def make_and_check_hashes(which: str):
    current = hasher.make_hashes(which=which)
    expected = hasher.read_expected_hashes(which=which)
    assert current.equals(expected)


def test_get_emissions_data():
    make_and_check_hashes("CEF")


def test_get_emissions(mocker):
    config = dict(year=2019, freq="60min", country="DE")

    tl = [
        ("_EP", "elmada.el_entsoepy.prep_XEFs", config),
        ("_PP", "elmada.el_opsd.prep_CEFs", config),
        ("_PWL", "elmada.el_EU_PWL_CEFs.prep_CEFs", dict(**config, validation_mode=False)),
        ("_PWLv", "elmada.el_EU_PWL_CEFs.prep_CEFs", dict(**config, validation_mode=True)),
    ]

    for (method, func, kwargs) in tl:
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


@pytest.mark.slow
@pytest.mark.parametrize(
    "method,expected_keys", [("PP", pp_keys), ("PWL", pwl_keys), ("PWLv", pwl_keys)]
)
def test_get_merit_order(method, expected_keys):
    df = elmada.get_merit_order(year=2019, country="DE", method=method)
    assert isinstance(df, pd.DataFrame)
    df.keys().equals(expected_keys)


country_load_means = [
    ("AT", 7201),
    ("BE", 9697),
    ("CZ", 7554),
    ("DE", 56424),
    ("DK", 3828),
    ("ES", 28537),
    ("FI", 9525),
    ("FR", 53379),
    ("GB", 34018),
    ("GR", 5899),
    ("HU", 4970),
    ("IE", 3317),
    ("IT", 33578),
    ("LT", 1389),
    ("NL", 12405),
    ("PL", 19282),
    ("PT", 5745),
    ("RO", 6859),
    ("RS", 4490),
    ("SI", 1496),
]


@pytest.mark.parametrize("country,mean", country_load_means)
def test_get_el_national_load(country, mean):
    assert int(elmada.get_el_national_load(year=2019, country=country).mean()) == mean


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
def test_get_residual_load(country, mean):
    assert int(elmada.get_residual_load(year=2019, country=country).mean()) == mean


@pytest.mark.slow
def test_get_el_national_generation():
    make_and_check_hashes("GEN")


def test_get_prices(mocker):
    config = dict(year=2019, freq="60min", country="DE", cache=True)
    ep_mock = mocker.patch("elmada.el_entsoepy.prep_dayahead_prices", return_value=True)
    assert elmada.get_prices(**config, method="hist_EP")
    ep_mock.assert_called_once_with(**config)

    sm_mock = mocker.patch("elmada.el_smard.prep_dayahead_prices", return_value=True)
    assert elmada.get_prices(**config, method="hist_SM")
    sm_mock.assert_called_once_with(**config)

    pp_mock = mocker.patch("elmada.main.get_emissions", return_value={"marginal_cost": True})
    elmada.get_prices(**config, method="PP")
    pp_mock.assert_called_once_with(**config, method="_PP")

    pwl_mock = mocker.patch("elmada.main.get_emissions", return_value={"marginal_cost": True})
    elmada.get_prices(**config, method="PWL")
    pwl_mock.assert_called_once_with(**config, method="_PWL")
