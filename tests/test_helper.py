import pandas as pd
import pytest
from elmada import helper as hp
import elmada
from elmada import paths


@pytest.mark.parametrize(
    "freq, year, month, day, expected",
    [["60min", 2020, 6, 6, 3768], ["30min", 1990, 3, 12, 3360], ["15min", 1999, 1, 1, 0]],
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


@pytest.mark.parametrize("freq, expected", [["60min", 1.0], ["30min", 0.5], ["15min", 0.25]])
def test_freq_to_hours(freq: str, expected: float):
    assert hp.freq_to_hours(freq=freq) == expected


def test_fill_outlier_and_nan():
    ser = pd.Series(6 * [1] + [50] + 4 * [2])
    assert ser[6] == 50
    assert hp.fill_outlier_and_nan(ser, method="linear")[6] == 1.5
    assert hp.fill_outlier_and_nan(ser, method="fill")[6] == 2


def test_delete_cache(mocker, capsys):

    hp.delete_cache("XXXX")
    captured = capsys.readouterr()
    assert captured.out == "No file found containing 'XXXX'.\n"

    fp = paths.CACHE_DIR / "test_file_XXXX.h5"
    tuplelist = [(True, "1 files deleted\n"), (False, "No files deleted\n")]

    for (patch_value, msg) in tuplelist:
        fp.touch(exist_ok=True)
        assert fp.exists()
        mocker.patch("elmada.helper.confirm_deletion", return_value=patch_value)
        hp.delete_cache("test_file_XXXX")
        captured = capsys.readouterr()
        assert msg in captured.out

    try:
        fp.unlink()
    except FileNotFoundError:
        pass

    assert not fp.exists()


def test_print_error(capsys):
    a = pd.Series(10, range(10))
    b = a * 1.1
    hp.print_error(a, b)
    captured = capsys.readouterr()
    captured.out == "relative error = 10.00%, absolute error= 1.00 t CO2/MWh.\n"


def test_add_row_for_steps():
    ser = pd.Series(range(5))
    result = hp.add_row_for_steps(ser)
    assert len(result) == 6
    assert result.iloc[0] == 0


def test_sizeof_fmt():
    assert hp.sizeof_fmt(5000) == "5.0 KB"
    assert hp.sizeof_fmt(2e24) == "2.0 YB"


def test_write_array():
    ser = pd.Series(range(4))
    path_scheme = paths.CACHE_DIR / "test_file_XXX.suffix"

    with pytest.raises(RuntimeError):
        hp.write_array(ser, path_scheme)

    for suffix in [".h5", ".csv"]:
        fp = path_scheme.with_suffix(suffix)
        assert not fp.exists()
        hp.write_array(ser, fp)
        assert fp.exists()
        fp.unlink()
