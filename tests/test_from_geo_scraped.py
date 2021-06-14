import pandas as pd

from elmada import from_geo_scraped

from .common.hasher import get_hash


def test_get_pp_sizes_for_pwl():
    df = from_geo_scraped.get_pp_sizes_for_pwl()
    assert get_hash(df) == "f8ea5251f2"


def test_get_pp_sizes():
    df = from_geo_scraped.get_pp_sizes()
    assert get_hash(df) == "fcf6b2ba28"


def test_get_units_of_geo_list():
    df = from_geo_scraped.get_units_of_geo_list(cache=True)
    expected = pd.Index(
        ["cy", "fuel", "geoid", "capa", "eff", "commissioned", "unit_no"], dtype="object"
    )
    assert df.keys().equals(expected)


def test__query_geo_power_plant_data(mocker):
    mock = mocker.patch("elmada.from_geo_scraped.get_df_from_geo_id", return_value=pd.DataFrame())
    from_geo_scraped._query_geo_power_plant_data()
    mock.assert_called()


def test_get_df_from_geo_id():
    # NOTE: Requires internet connection
    df = from_geo_scraped.get_df_from_geo_id(45151)
    assert get_hash(df) == "f6be9a1b2b"
