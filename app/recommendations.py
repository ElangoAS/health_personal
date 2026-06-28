from __future__ import annotations

from typing import Any

import pandas as pd


def generate_recommendation(df: pd.DataFrame) -> list[str]:
    """Generate coaching insights from a processed activity DataFrame."""
    if df is None or df.empty:
        return ["No training data is available yet. Log some runs to unlock insights."]

    if "start_date" not in df.columns:
        return ["The activity data is missing a date column, so no recommendations can be generated."]

    df = df.copy()
    df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")
    df = df.dropna(subset=["start_date"])

    if df.empty:
        return ["No usable training data is available yet."]

    week = df.set_index("start_date").resample("W")["distance_km"].sum().dropna()
    if week.empty:
        return ["No weekly distance data is available yet."]

    recent_week = week.iloc[-1]
    prior_week = week.iloc[-2] if len(week) > 1 else None
    avg_pace = df["pace_min_per_km"].dropna().mean()
    avg_heart_rate = df["average_heartrate"].dropna().mean() if "average_heartrate" in df.columns else None

    insights: list[str] = []

    if prior_week is not None and recent_week > prior_week * 1.20:
        insights.append(
            f"Weekly distance increased by {((recent_week / prior_week) - 1) * 100:.1f}%. Consider a lighter week to avoid overtraining."
        )
    elif prior_week is not None and recent_week < prior_week * 0.9:
        insights.append(
            "This week was a step back in volume. Keep the recovery focus and build back gradually."
        )
    else:
        insights.append("Training volume is steady. A modest increase in one key workout can support progress.")

    if avg_pace:
        recent_pace = df.sort_values("start_date").tail(3)["pace_min_per_km"].dropna().mean()
        earlier_pace = df.sort_values("start_date").head(3)["pace_min_per_km"].dropna().mean()
        if pd.notna(recent_pace) and pd.notna(earlier_pace) and recent_pace > earlier_pace * 1.05:
            insights.append("Your recent pace is slipping compared with earlier runs. Prioritize recovery and easy mileage.")
        else:
            insights.append("Recent pace trends look stable. Keep consistency high and add a small strength block.")

    if avg_heart_rate is not None:
        if avg_heart_rate > 165:
            insights.append("Average heart rate is elevated. Ensure you are not training too hard on easy days.")
        else:
            insights.append("Heart rate looks reasonable for your training. Monitor it during harder sessions.")

    if prior_week is not None:
        insights.append(f"Weekly distance last week: {prior_week:.1f} km, this week: {recent_week:.1f} km.")

    return insights
