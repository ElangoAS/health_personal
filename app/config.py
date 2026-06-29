import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"
load_dotenv(ENV_FILE, override=False)


def _load_streamlit_secrets() -> None:
    """Load Streamlit Cloud secrets into the environment when available."""
    try:
        import streamlit as st

        for key, value in st.secrets.items():
            if isinstance(value, (str, int, float, bool)):
                os.environ.setdefault(str(key), str(value))
    except Exception:
        return


_load_streamlit_secrets()


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


def get_list_setting(name: str) -> list[str]:
    """Read a comma-separated list from the environment."""
    value = get_setting(name)
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def is_google_auth_configured() -> bool:
    """Return True when Streamlit Google OIDC auth settings are present."""
    try:
        import streamlit as st

        auth = st.secrets.get("auth", {})
        if auth.get("client_id") and auth.get("client_secret"):
            return True
    except Exception:
        pass
    return bool(get_setting("AUTH_CLIENT_ID") and get_setting("AUTH_CLIENT_SECRET"))


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
ALLOWED_EMAILS = get_list_setting("ALLOWED_EMAILS")
