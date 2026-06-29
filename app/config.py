import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"
load_dotenv(ENV_FILE, override=False)


def get_setting(name: str, default: str | None = None) -> str:
    """Read a setting from the environment with a fallback default."""
    value = os.getenv(name)
    if value is None:
        value = os.getenv(name.upper())
    if value is None:
        value = os.getenv(name.lower())
    if value is None:
        value = default or ""
    return value


def get_bool_setting(name: str, default: bool = False) -> bool:
    """Read a boolean setting from the environment."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


STRAVA_ACCESS_TOKEN = get_setting("STRAVA_ACCESS_TOKEN")
STRAVA_REFRESH_TOKEN = get_setting("STRAVA_REFRESH_TOKEN")
CLIENT_ID = get_setting("CLIENT_ID")
CLIENT_SECRET = get_setting("CLIENT_SECRET")
OPENAI_ENDPOINT = get_setting("OPENAI_ENDPOINT")
OPENAI_DEPLOYMENT_NAME = get_setting("OPENAI_DEPLOYMENT_NAME")
OPENAI_API_KEY = get_setting("OPENAI_API_KEY")
OPENAI_MODEL = get_setting("OPENAI_MODEL")
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "running_coach.db"
CACHE_DIR = DATA_DIR / "cache"
LOGS_DIR = BASE_DIR / "logs"
LOG_FILE = LOGS_DIR / "app.log"
CACHE_ENABLED = get_bool_setting("CACHE_ENABLED", True)
