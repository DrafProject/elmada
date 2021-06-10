from elmada import from_smard
import pandas as pd


def test_prep_dayahead_prices():
    result = from_smard.prep_dayahead_prices(year=2018, country="DE", cache=False)
    assert isinstance(result, pd.Series)
    result = from_smard.prep_dayahead_prices(year=2015, country="DE", cache=False)
    assert isinstance(result, pd.Series)
