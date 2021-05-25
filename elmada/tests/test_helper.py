from elmada import helper as hp
import pandas as pd
import pytest

datetime_to_int_container = [
    ["60min", 2020, 6, 6, 3768],
    ["30min", 1990, 3, 12, 3360],
    ["15min", 1999, 1, 1, 0],
]


@pytest.mark.parametrize("freq, year, month, day, expected", datetime_to_int_container)
def test_datetime_to_int(freq: str, year: int, month: int, day: int, expected: int):
    assert hp.datetime_to_int(freq, year, month, day) == expected


int_to_datetime_container = [
    ["15min", 1999, 10, pd.Timestamp("1999-01-01 02:30:00", freq="15T")],
    ["45min", 2003, 34, pd.Timestamp("2003-01-02 01:30:00", freq="45T")],
    ["60min", 2020, 1, pd.Timestamp("2020-01-01 01:00:00", freq="60T")],
]


@pytest.mark.parametrize("freq, year, pos, expected", int_to_datetime_container)
def test_int_to_datetime(freq: str, year: int, pos: int, expected: pd.Timestamp):
    assert hp.int_to_datetime(freq=freq, year=year, pos=pos) == expected


make_datetimeindex_container = [[2019, "60min", None], [1999, "15min", None], [2099, "45min", None]]


@pytest.mark.parametrize("year, freq, tz", make_datetimeindex_container)
def test_make_datetimeindex(year: int, freq: str, tz: str):
    assert isinstance(hp.make_datetimeindex(year=year, freq=freq, tz=tz), pd.DatetimeIndex)


int_from_freq_container = [["60min", 60], ["30min", 30], ["45min", 45], ["15min", 15]]


@pytest.mark.parametrize("freq, expected", int_from_freq_container)
def test_int_from_freq(freq: str, expected: int):
    assert hp.int_from_freq(freq=freq) == expected


sizeof_fmt_container = [
    [1.0, "Will be changed", "  1.0 B"],
    [14.77, "AAA", " 14.8 AAA"],
    [99.99993, "Suff", "100.0 Suff"],
]


@pytest.mark.parametrize("num, suffix, expected", sizeof_fmt_container)
def test_sizeof_fmt(num: float, suffix: str, expected: str):
    if suffix == "Will be changed":
        assert hp.sizeof_fmt(num=num) == expected
    else:
        assert hp.sizeof_fmt(num=num, suffix=suffix) == expected


freq_to_hours_container = [["60min", 1.0], ["30min", 0.5], ["15min", 0.25]]


@pytest.mark.parametrize("freq, expected", freq_to_hours_container)
def test_freq_to_hours(freq: str, expected: float):
    assert hp.freq_to_hours(freq=freq) == expected
