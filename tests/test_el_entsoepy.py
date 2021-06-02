import pytest
from elmada import el_entsoepy as ep

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
def test_prep_residual_load(country, mean):
    assert int(ep.prep_residual_load(year=2019, country=country).mean()) == mean
