from typing import Any, List

import pandas as pd


def activities_to_dataframe(activities: List[dict[str, Any]]) -> pd.DataFrame:
    """Convert raw Strava activity payloads into a processed DataFrame."""
    if not activities:
        return pd.DataFrame(
            columns=[
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
        )

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
    return processed_df.sort_values("start_date").reset_index(drop=True)
