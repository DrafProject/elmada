from typing import Optional
from appdirs import user_cache_dir
from pathlib import Path
from elmada.mode import is_safe_mode


def _get_cache_directory() -> Path:
    """Returns the path to cache directory and creates it, if not yet existing."""
    fp = Path(user_cache_dir(appname="Elmada", appauthor="DrafProject"))
    fp.mkdir(parents=True, exist_ok=True)
    return fp


def _get_base_dir():
    return Path(__file__).resolve().parent


CACHE_DIR = _get_cache_directory()
BASE_DIR = _get_base_dir()
KEYS_DIR = BASE_DIR / "api_keys"
DATA_DIR = BASE_DIR / "data/raw"
SAFE_CACHE_DIR = BASE_DIR / "data/safe_cache"


def mode_dependent_cache_dir(year: Optional[int] = None):
    is_safe_year = year in range(2017, 2021)
    return SAFE_CACHE_DIR if (is_safe_mode() and is_safe_year) else CACHE_DIR
