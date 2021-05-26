from elmada import mappings as mp
from .common.hasher import make_cef_hashes, read_target_cef_hashes


def test_cef_data_integrity():
    current = make_cef_hashes()
    target = read_target_cef_hashes()
    assert current.equals(target)
