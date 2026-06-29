from unittest.mock import MagicMock, patch

import pandas as pd

from app.pipeline import run_pipeline


@patch("app.pipeline.init_db")
@patch("app.pipeline.StravaClient")
@patch("app.pipeline.activities_to_dataframe")
@patch("app.pipeline.replace_activities")
@patch("app.pipeline.record_pipeline_run")
def test_run_pipeline_success(
    mock_record_run,
    mock_replace_activities,
    mock_to_dataframe,
    mock_client_cls,
    mock_init_db,
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "running_coach.db"
    monkeypatch.setattr("app.pipeline.DATABASE_PATH", db_path)
    mock_init_db.return_value = db_path

    mock_client = MagicMock()
    mock_client.get_all_activities.return_value = [{"id": 1}]
    mock_client_cls.return_value = mock_client

    mock_to_dataframe.return_value = pd.DataFrame(
        {
            "id": [1],
            "distance_km": [5.0],
            "pace_min_per_km": [5.0],
            "start_date": ["2026-06-28"],
        }
    )

    result = run_pipeline()

    assert result["status"] == "ok"
    assert result["total_runs"] == 1
    mock_replace_activities.assert_called_once()
    mock_record_run.assert_called_once()
