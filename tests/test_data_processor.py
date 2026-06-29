import pandas as pd

from app.data_processor import activities_to_dataframe


def test_process_empty_activities():
    df = activities_to_dataframe([])
    assert df.empty


def test_process_activities_generates_fields():
    payload = [
        {
            "id": 123,
            "name": "Easy run",
            "start_date_local": "2026-06-27T07:00:00Z",
            "distance": 5000,
            "moving_time": 1500,
            "average_speed": 3.2,
            "average_heartrate": 150,
        }
    ]
    df = activities_to_dataframe(payload)
    assert len(df) == 1
    assert df.loc[0, "distance_km"] == 5.0
    assert df.loc[0, "duration_minutes"] == 25.0
    assert df.loc[0, "pace_min_per_km"] == 5.0
    assert df.loc[0, "average_heartrate"] == 150
