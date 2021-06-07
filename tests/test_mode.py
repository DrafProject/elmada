import pytest
from elmada import mode
import elmada


def test_set_mode():
    mode_backup = mode.get_mode()

    mode.set_mode("safe")
    assert mode.get_mode() == "safe"

    mode.set_mode("live")
    assert mode.get_mode() == "live"

    with pytest.raises(AssertionError):
        mode.set_mode("save")

    mode.set_mode(mode_backup)


def test_is_safe_mode(mocker):
    mocker.patch("elmada.mode.get_mode", return_value="safe")
    assert mode.is_safe_mode()
