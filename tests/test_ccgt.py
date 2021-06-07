import collections

import elmada.el_share_CCGT as ccgt
import pandas as pd


def test_get_ccgt_shares_from_cascade():
    df = ccgt.get_ccgt_shares_from_cascade()
    assert isinstance(df, pd.DataFrame)


def test_get_wiki_shares():
    result = ccgt.get_wiki_shares(cache=False)
    assert isinstance(result, pd.Series)


def get_geo_shares_overview():
    result = ccgt.get_geo_shares_overview()
    assert isinstance(result, pd.DataFrame)


def test_get_valid_countries():
    result = ccgt.get_valid_countries()
    assert isinstance(result, collections.OrderedDict)


def test_get_geo_list():
    result = ccgt.get_geo_list()
    assert isinstance(result, pd.DataFrame)


def test_get_geo_shares_overview():
    ccgt.get_geo_shares_overview()
