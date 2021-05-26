import elmada
import pandas as pd
from elmada import geo_scraper as gs
from .common.hasher import get_hash


def test_get_pp_sizes_for_pwl():
    df = gs.get_pp_sizes_for_pwl()
    assert get_hash(df) == "f8ea5251f2"


def test_get_pp_sizes():
    df = gs.get_pp_sizes()
    assert get_hash(df) == "fcf6b2ba28"


def test_get_units_of_geo_list():
    df = gs.get_units_of_geo_list()
    target = pd.Index(
        ["cy", "fuel", "geoid", "capa", "eff", "commissioned", "unit_no"], dtype="object"
    )
    assert df.keys().equals(target)


def test_get_df_from_geo_id():
    df = gs.get_df_from_geo_id(45151)
    assert get_hash(df) == "f6be9a1b2b"
