import json
from pathlib import Path
from typing import Any, List, Tuple

import pandas as pd

try:
    from .config import DATA_DIR
except ImportError:  # pragma: no cover
    from config import DATA_DIR

from .utils import ensure_directory, timestamp, versioned_filename


def process_activities(
    activities: List[dict[str, Any]], output_dir: Path | None = None
) -> Tuple[pd.DataFrame, str, str]:
    """Convert raw Strava activity payloads into a processed DataFrame and save artifacts."""
    output_path = Path(output_dir or DATA_DIR)
    ensure_directory(output_path)

    if not activities:
        empty_df = pd.DataFrame(
            columns=[
                "id",
                "name",
                "start_date",
                "distance_km",
                "duration_minutes",
                "pace_min_per_km",
                "average_heartrate",
            ]
        )
        stamp = timestamp()
        raw_path = output_path / versioned_filename("raw_activities", "json", stamp)
        processed_path = output_path / versioned_filename("processed_activities", "csv", stamp)
        raw_path.write_text("[]", encoding="utf-8")
        empty_df.to_csv(processed_path, index=False)
        return empty_df, str(processed_path), str(raw_path)

    df = pd.DataFrame(activities)
    if "id" not in df.columns:
        df["id"] = range(1, len(df) + 1)

    date_column = "start_date_local" if "start_date_local" in df.columns else "start_date"
    df["start_date"] = pd.to_datetime(df[date_column], errors="coerce")

    df["distance_km"] = pd.to_numeric(df.get("distance"), errors="coerce") / 1000.0
    df["duration_minutes"] = pd.to_numeric(df.get("moving_time"), errors="coerce") / 60.0
    df["pace_min_per_km"] = (
        df["duration_minutes"] / df["distance_km"]
    ).where(df["distance_km"] > 0, None)

    selected_columns = [
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

    available_columns = [col for col in selected_columns if col in df.columns]
    processed_df = df[available_columns].copy()
    processed_df = processed_df.sort_values("start_date").reset_index(drop=True)

    stamp = timestamp()
    raw_path = output_path / versioned_filename("raw_activities", "json", stamp)
    processed_path = output_path / versioned_filename("processed_activities", "csv", stamp)

    raw_path.write_text(json.dumps(activities, indent=2), encoding="utf-8")
    processed_df.to_csv(processed_path, index=False)
    return processed_df, str(processed_path), str(raw_path)
