from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import DATA_DIR
from .data_processor import process_activities
from .recommendations import generate_recommendation
from .strava_client import StravaClient
from .utils import ensure_directory, setup_logging, timestamp


def main() -> None:
    """Run the full Strava ingestion and analytics pipeline."""
    logger = setup_logging()
    ensure_directory(DATA_DIR)

    client = StravaClient()
    try:
        activities = client.get_all_activities(per_page=100, max_pages=5)
    except Exception as exc:  # pragma: no cover
        logger.exception("Failed to fetch activities: %s", exc)
        print({"status": "error", "message": str(exc)})
        return

    df, processed_path, raw_path = process_activities(activities, DATA_DIR)

    recommendations = generate_recommendation(df)
    summary = {
        "status": "ok",
        "total_runs": int(len(df)),
        "processed_file": processed_path,
        "raw_file": raw_path,
        "recommendations": recommendations,
    }

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
