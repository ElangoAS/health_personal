from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .config import DATABASE_PATH
from .data_processor import activities_to_dataframe
from .db import get_last_pipeline_run, init_db, record_pipeline_run, replace_activities
from .recommendations import generate_recommendation
from .strava_client import StravaClient
from .utils import setup_logging


def get_last_run() -> dict[str, Any] | None:
    """Return metadata from the most recent pipeline execution."""
    return get_last_pipeline_run()


def run_pipeline(per_page: int = 100, max_pages: int = 5) -> dict[str, Any]:
    """Fetch Strava activities, process them, and store them in SQLite."""
    logger = setup_logging()
    init_db()

    client = StravaClient()
    try:
        activities = client.get_all_activities(per_page=per_page, max_pages=max_pages)
    except Exception as exc:  # pragma: no cover
        logger.exception("Failed to fetch activities: %s", exc)
        summary = {
            "status": "error",
            "message": str(exc),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
        record_pipeline_run(summary)
        return summary

    df = activities_to_dataframe(activities)
    replace_activities(df, activities)
    recommendations = generate_recommendation(df)
    summary = {
        "status": "ok",
        "total_runs": int(len(df)),
        "database": str(DATABASE_PATH),
        "recommendations": recommendations,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    record_pipeline_run(summary)
    logger.info("Pipeline completed: %s runs saved to %s", summary["total_runs"], DATABASE_PATH)
    return summary
