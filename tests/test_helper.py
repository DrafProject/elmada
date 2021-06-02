import pandas as pd
import pytest
from elmada import helper as hp


@pytest.mark.parametrize(
    "freq, year, month, day, expected",
    [["60min", 2020, 6, 6, 3768], ["30min", 1990, 3, 12, 3360], ["15min", 1999, 1, 1, 0],],
)
def test_datetime_to_int(freq: str, year: int, month: int, day: int, expected: int):
    assert hp.datetime_to_int(freq, year, month, day) == expected


@pytest.mark.parametrize(
    "freq, year, pos, expected",
    [
        ["15min", 1999, 10, pd.Timestamp("1999-01-01 02:30:00", freq="15T")],
        ["45min", 2003, 34, pd.Timestamp("2003-01-02 01:30:00", freq="45T")],
        ["60min", 2020, 1, pd.Timestamp("2020-01-01 01:00:00", freq="60T")],
    ],
)
def test_int_to_datetime(freq: str, year: int, pos: int, expected: pd.Timestamp):
    assert hp.int_to_datetime(freq=freq, year=year, pos=pos) == expected


@pytest.mark.parametrize(
    "year, freq, tz", [[2019, "60min", None], [1999, "15min", None], [2099, "45min", None]]
)
def test_make_datetimeindex(year: int, freq: str, tz: str):
    assert isinstance(hp.make_datetimeindex(year=year, freq=freq, tz=tz), pd.DatetimeIndex)


@pytest.mark.parametrize(
    "freq, expected", [["60min", 60], ["30min", 30], ["45min", 45], ["15min", 15]]
)
def test_int_from_freq(freq: str, expected: int):
    assert hp.int_from_freq(freq=freq) == expected


@pytest.mark.parametrize(
    "num, suffix, expected",
    [
        [1.0, "Will be changed", "  1.0 B"],
        [14.77, "AAA", " 14.8 AAA"],
        [99.99993, "Suff", "100.0 Suff"],
    ],
)
def test_sizeof_fmt(num: float, suffix: str, expected: str):
    if suffix == "Will be changed":
        assert hp.sizeof_fmt(num=num) == expected
    else:
        assert hp.sizeof_fmt(num=num, suffix=suffix) == expected


@pytest.mark.parametrize("freq, expected", [["60min", 1.0], ["30min", 0.5], ["15min", 0.25]])
def test_freq_to_hours(freq: str, expected: float):
    assert hp.freq_to_hours(freq=freq) == expected
