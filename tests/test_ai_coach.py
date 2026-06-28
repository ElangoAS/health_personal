import pandas as pd

from app.ai_coach import AIRunningCoach


def test_build_context_handles_missing_optional_fields():
    """Context builder must not fail when prior week or heart rate are unavailable."""
    coach = object.__new__(AIRunningCoach)
    data = {
        "start_date": ["2026-06-27T07:00:00Z"],
        "distance_km": [5.0],
        "duration_minutes": [25.0],
        "pace_min_per_km": [5.0],
    }
    df = pd.DataFrame(data)

    context = coach._build_context(df)

    assert "Total runs: 1" in context
    assert "Last week: N/A" in context
    assert "Average heart rate: N/A" in context


def test_build_context_handles_none_numeric_values():
    """Context builder must not fail when numeric fields are None."""
    coach = object.__new__(AIRunningCoach)
    data = {
        "start_date": ["2026-06-27T07:00:00Z"],
        "distance_km": [None],
        "duration_minutes": [None],
        "pace_min_per_km": [None],
        "average_heartrate": [None],
    }
    df = pd.DataFrame(data)

    context = coach._build_context(df)

    assert "Total runs: 1" in context
    assert "N/A" in context
