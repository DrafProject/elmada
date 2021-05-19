class ConfigUtil:
    mode = "live"


def set_mode(mode: str):
    assert mode in ["safe", "live"]
    ConfigUtil.mode = mode


def get_mode() -> str:
    return ConfigUtil.mode
