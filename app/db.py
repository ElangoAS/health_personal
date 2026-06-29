from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from .config import DATA_DIR, DATABASE_PATH
except ImportError:  # pragma: no cover
    from config import DATA_DIR, DATABASE_PATH

from .utils import ensure_directory, get_latest_csv

SCHEMA = """
CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY,
    name TEXT,
    type TEXT,
    start_date TEXT,
    distance_km REAL,
    duration_minutes REAL,
    pace_min_per_km REAL,
    average_speed REAL,
    average_heartrate REAL,
    raw_json TEXT,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status TEXT NOT NULL,
    total_runs INTEGER,
    message TEXT,
    completed_at TEXT NOT NULL
);
"""

ACTIVITY_COLUMNS = [
    "id",
    "name",
    "type",
    "start_date",
    "distance_km",
    "duration_minutes",
    "pace_min_per_km",
    "average_speed",
    "average_heartrate",
]


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Open a SQLite connection to the application database."""
    path = db_path or DATABASE_PATH
    ensure_directory(path.parent)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def _ensure_schema(db_path: Path) -> None:
    """Create database tables if they do not already exist."""
    ensure_directory(db_path.parent)
    with get_connection(db_path) as connection:
        connection.executescript(SCHEMA)
        connection.commit()


def init_db(db_path: Path | None = None, migrate: bool = True) -> Path:
    """Initialize the database and optionally import legacy CSV data."""
    path = db_path or DATABASE_PATH
    _ensure_schema(path)
    if migrate:
        migrate_csv_if_empty(path)
    return path


def migrate_csv_if_empty(db_path: Path | None = None) -> bool:
    """Import the latest processed CSV when the database has no activities yet."""
    path = db_path or DATABASE_PATH
    if has_activities(path):
        return False

    latest_csv = get_latest_csv(DATA_DIR)
    if latest_csv is None:
        return False

    df = pd.read_csv(latest_csv, parse_dates=["start_date"])
    if df.empty:
        return False

    replace_activities(df, raw_activities=[], db_path=path)
    record_pipeline_run(
        {
            "status": "ok",
            "total_runs": int(len(df)),
            "message": f"Migrated from {latest_csv.name}",
        },
        db_path=path,
    )
    return True


def has_activities(db_path: Path | None = None) -> bool:
    """Return whether any activities are stored in the database."""
    path = db_path or DATABASE_PATH
    if not path.exists():
        return False
    with get_connection(path) as connection:
        row = connection.execute("SELECT COUNT(*) AS count FROM activities").fetchone()
    return bool(row and row["count"] > 0)


def replace_activities(
    df: pd.DataFrame,
    raw_activities: list[dict[str, Any]],
    db_path: Path | None = None,
) -> int:
    """Replace all stored activities with the latest fetched snapshot."""
    path = db_path or DATABASE_PATH
    _ensure_schema(path)

    raw_by_id = {activity.get("id"): activity for activity in raw_activities}
    updated_at = datetime.now(timezone.utc).isoformat()

    with get_connection(path) as connection:
        connection.execute("DELETE FROM activities")
        for _, row in df.iterrows():
            activity_id = int(row["id"])
            connection.execute(
                """
                INSERT INTO activities (
                    id, name, type, start_date, distance_km, duration_minutes,
                    pace_min_per_km, average_speed, average_heartrate, raw_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    activity_id,
                    row.get("name"),
                    row.get("type"),
                    pd.Timestamp(row["start_date"]).isoformat() if pd.notna(row.get("start_date")) else None,
                    row.get("distance_km"),
                    row.get("duration_minutes"),
                    row.get("pace_min_per_km"),
                    row.get("average_speed"),
                    row.get("average_heartrate"),
                    json.dumps(raw_by_id.get(activity_id, {})),
                    updated_at,
                ),
            )
        connection.commit()
    return int(len(df))


def load_activities_df(db_path: Path | None = None) -> pd.DataFrame:
    """Load all activities from SQLite into a DataFrame."""
    path = db_path or DATABASE_PATH
    init_db(path)

    query = f"""
        SELECT {", ".join(ACTIVITY_COLUMNS)}
        FROM activities
        ORDER BY start_date
    """
    with get_connection(path) as connection:
        df = pd.read_sql_query(query, connection, parse_dates=["start_date"])

    if df.empty:
        return pd.DataFrame(columns=ACTIVITY_COLUMNS)

    if "pace_min_per_km" not in df.columns:
        df["pace_min_per_km"] = None
    return df.reset_index(drop=True)


def record_pipeline_run(summary: dict[str, Any], db_path: Path | None = None) -> None:
    """Persist metadata about a pipeline execution."""
    path = db_path or DATABASE_PATH
    _ensure_schema(path)
    completed_at = summary.get("completed_at") or datetime.now(timezone.utc).isoformat()

    with get_connection(path) as connection:
        connection.execute(
            """
            INSERT INTO pipeline_runs (status, total_runs, message, completed_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                summary.get("status", "unknown"),
                summary.get("total_runs"),
                summary.get("message"),
                completed_at,
            ),
        )
        connection.commit()


def get_last_pipeline_run(db_path: Path | None = None) -> dict[str, Any] | None:
    """Return metadata from the most recent pipeline execution."""
    path = db_path or DATABASE_PATH
    if not path.exists():
        return None

    with get_connection(path) as connection:
        row = connection.execute(
            """
            SELECT status, total_runs, message, completed_at
            FROM pipeline_runs
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

    if row is None:
        return None
    return dict(row)
