class ConfigUtil:
    mode = "safe"


def set_mode(mode: str):
    """Set data mode either to 'safe' or to 'live'."""
    assert mode in ["safe", "live"]
    ConfigUtil.mode = mode


def get_mode() -> str:
    return ConfigUtil.mode


def is_safe_mode() -> bool:
    return get_mode() == "safe"
