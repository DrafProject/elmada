import collections

from elmada import cc_share
import pandas as pd


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
    result = cc_share.get_geo_list()
    assert isinstance(result, pd.DataFrame)


def test_get_geo_shares_overview():
    cc_share.get_geo_shares_overview()
