import pandas as pd

from app.data_processor import process_activities


def test_process_empty_activities(tmp_path):
    df, processed_path, raw_path = process_activities([], tmp_path)
    assert df.empty
    assert "processed_activities_" in processed_path
    assert "raw_activities_" in raw_path
    loaded = pd.read_csv(processed_path)
    assert loaded.empty


def test_process_activities_generates_fields(tmp_path):
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
    df, processed_path, raw_path = process_activities(payload, tmp_path)
    assert len(df) == 1
    assert df.loc[0, "distance_km"] == 5.0
    assert df.loc[0, "duration_minutes"] == 25.0
    assert df.loc[0, "pace_min_per_km"] == 5.0
    assert df.loc[0, "average_heartrate"] == 150
