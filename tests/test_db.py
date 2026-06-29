import pandas as pd

from app.db import init_db, migrate_csv_if_empty, replace_activities


def test_migrate_csv_if_empty(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    db_path = data_dir / "running_coach.db"
    csv_path = data_dir / "processed_activities_20260628_120000.csv"
    csv_path.write_text(
        "id,name,type,start_date,distance_km,duration_minutes,pace_min_per_km,average_speed,average_heartrate\n"
        "1,Morning Run,Run,2026-06-28,5.0,25.0,5.0,3.2,150\n",
        encoding="utf-8",
    )

    monkeypatch.setattr("app.db.DATA_DIR", data_dir)
    monkeypatch.setattr("app.db.DATABASE_PATH", db_path)
    monkeypatch.setattr("app.utils.DATA_DIR", data_dir)

    migrated = migrate_csv_if_empty(db_path=db_path)

    assert migrated is True
    init_db(db_path)
    from app.db import load_activities_df

    df = load_activities_df(db_path=db_path)
    assert len(df) == 1
    assert df.loc[0, "name"] == "Morning Run"


def test_migrate_csv_skips_when_db_has_data(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    db_path = data_dir / "running_coach.db"
    monkeypatch.setattr("app.db.DATA_DIR", data_dir)
    monkeypatch.setattr("app.db.DATABASE_PATH", db_path)

    replace_activities(
        pd.DataFrame(
            {
                "id": [99],
                "name": ["Existing"],
                "type": ["Run"],
                "start_date": [pd.Timestamp("2026-06-01")],
                "distance_km": [3.0],
                "duration_minutes": [18.0],
                "pace_min_per_km": [6.0],
                "average_speed": [2.8],
                "average_heartrate": [140],
            }
        ),
        [],
        db_path=db_path,
    )

    migrated = migrate_csv_if_empty(db_path=db_path)
    assert migrated is False
