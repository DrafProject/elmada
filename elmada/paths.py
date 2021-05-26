from appdirs import user_cache_dir
from pathlib import Path


def get_cache_directory() -> Path:
    """Returns the path to cache directory and creates it, if not yet existing."""
    fp = Path(user_cache_dir(appname="Elmada", appauthor="DrafProject"))
    fp.mkdir(parents=True, exist_ok=True)
    return fp


CACHE_DIR = get_cache_directory()


def get_base_dir():
    return Path(__file__).resolve().parent


BASE_DIR = get_base_dir()
KEYS_DIR = BASE_DIR / "api_keys"
DATA_DIR = BASE_DIR / "data"
