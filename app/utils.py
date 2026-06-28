import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

try:
    from .config import DATA_DIR, LOG_FILE, LOGS_DIR
except ImportError:  # pragma: no cover
    from config import DATA_DIR, LOG_FILE, LOGS_DIR


def ensure_directory(path: Path) -> Path:
    """Create a directory if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Create a reusable logger that writes to file and console."""
    ensure_directory(LOGS_DIR)
    logger = logging.getLogger("strava_coach")
    if logger.handlers:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5_000_000, backupCount=3)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.propagate = False
    return logger


def timestamp() -> str:
    """Return a compact timestamp for file naming."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def get_latest_csv(data_dir: Optional[Path] = None) -> Optional[Path]:
    """Return the most recently created processed CSV file."""
    directory = data_dir or DATA_DIR
    if not directory.exists():
        return None
    csv_files = sorted(directory.glob("processed_activities_*.csv"))
    return csv_files[-1] if csv_files else None


def versioned_filename(prefix: str, extension: str, stamp: str) -> str:
    """Generate a versioned filename using a timestamp."""
    return f"{prefix}_{stamp}.{extension}"
