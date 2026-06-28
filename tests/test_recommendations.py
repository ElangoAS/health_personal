import pandas as pd

from app.recommendations import generate_recommendation


def test_generate_recommendation_empty():
    insights = generate_recommendation(pd.DataFrame())
    assert "No training data" in insights[0]


def test_generate_recommendation_stable_progress():
    data = {
        "start_date": ["2026-06-01", "2026-06-08", "2026-06-15"],
        "distance_km": [5.0, 5.2, 5.3],
        "pace_min_per_km": [5.0, 5.0, 4.9],
    }
    df = pd.DataFrame(data)
    insights = generate_recommendation(df)
    assert any("steady" in item.lower() for item in insights)


def test_generate_recommendation_heart_rate_warning():
    data = {
        "start_date": ["2026-06-01", "2026-06-08"],
        "distance_km": [5.0, 5.0],
        "pace_min_per_km": [5.0, 5.1],
        "average_heartrate": [170, 172],
    }
    df = pd.DataFrame(data)
    insights = generate_recommendation(df)
    assert any("elevated" in item.lower() for item in insights)
