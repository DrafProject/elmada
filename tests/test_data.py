import pytest

from .common import averages, hasher


def make_and_check_hashes(which: str) -> bool:
    current = hasher.make_hashes(which=which)
    expected = hasher.read_expected_hashes(which=which)
    return current.equals(expected)


# @pytest.mark.wantcache
# def test_emissions_data():
#     assert make_and_check_hashes("CEF")


def test_get_el_national_generation():
    assert make_and_check_hashes("GEN")


def test_averages():
    current = averages.make_avgs()
    expected = averages.read_expected_avgs()
    assert current.equals(expected)
