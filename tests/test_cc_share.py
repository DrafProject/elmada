import collections
from pathlib import Path

import pandas as pd

from elmada import cc_share


def test_get_ccgt_shares_from_cascade():
    df = cc_share.get_ccgt_shares_from_cascade()
    assert isinstance(df, pd.DataFrame)


def test_get_wiki_shares():
    result = cc_share.get_wiki_shares(cache=False)
    assert isinstance(result, pd.Series)


def get_geo_shares_overview():
    result = cc_share.get_geo_shares_overview()
    assert isinstance(result, pd.DataFrame)


def test_get_valid_countries():
    result = cc_share.get_valid_countries()
    assert isinstance(result, collections.OrderedDict)


def test_get_geo_list():
    result = cc_share.get_geo_list(cache=True)
    assert isinstance(result, pd.DataFrame)


def _read_fake_geo_body():
    fp = Path(__file__).parent / "common/geo_test_list.html"
    return fp.read_text()


def test__scrape_geo_list(response_mock):
    url = "http://globalenergyobservatory.org/list.php?db=PowerPlants&type=Gas"
    fake_geo_body = _read_fake_geo_body()
    with response_mock(f"GET {url} -> 200 :{fake_geo_body}"):
        df = cc_share.get_geo_list(cache=False)
    assert isinstance(df, pd.DataFrame)
    assert df.loc[1, "country"] == "Albania"
    print(df)


def test_get_geo_shares_overview():
    cc_share.get_geo_shares_overview()
