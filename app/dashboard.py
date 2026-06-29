from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path so imports work with streamlit run
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd
import streamlit as st

from app.ai_coach import AIRunningCoach
from app.db import has_activities, init_db, load_activities_df
from app.google_auth import render_auth_sidebar, require_google_auth
from app.pipeline import get_last_run, run_pipeline
from app.recommendations import generate_recommendation


st.set_page_config(page_title="AI Running Coach", page_icon="🏃", layout="wide")


@st.cache_data(show_spinner=False)
def load_data(data_version: str) -> pd.DataFrame:
    """Load activities from SQLite into a DataFrame."""
    _ = data_version
    init_db()
    return load_activities_df()


def _data_version(last_run: dict | None) -> str:
    """Build a cache key that changes when the database is refreshed."""
    if last_run and last_run.get("completed_at"):
        return str(last_run["completed_at"])
    return "empty"


def _format_last_sync(last_run: dict | None, latest_activity_date: pd.Timestamp | None = None) -> str:
    """Build a human-readable last-sync label for the dashboard."""
    parts: list[str] = []
    if last_run and last_run.get("completed_at"):
        parts.append(f"Last synced: {last_run['completed_at']}")
    if latest_activity_date is not None and pd.notna(latest_activity_date):
        parts.append(f"Latest run: {latest_activity_date.strftime('%Y-%m-%d %H:%M')}")
    return " | ".join(parts) if parts else "No data loaded yet"


def _fetch_latest_data() -> dict:
    """Fetch activities from Strava, store them, and clear cached dashboard data."""
    with st.spinner("Fetching latest activities from Strava..."):
        result = run_pipeline()
    load_data.clear()
    return result


def render() -> None:
    """Render the Streamlit dashboard."""
    require_google_auth()
    render_auth_sidebar()

    st.title("AI Running Coach Dashboard")

    st.sidebar.header("Data")
    if st.sidebar.button("Load latest data", type="primary", use_container_width=True):
        result = _fetch_latest_data()
        if result.get("status") == "ok":
            st.sidebar.success(f"Loaded {result['total_runs']} runs.")
        else:
            st.sidebar.error(result.get("message", "Failed to load data."))
        st.rerun()

    last_run = get_last_run()

    init_db()
    if not has_activities():
        st.caption("Track your training load, pace, and AI coaching insights")
        st.info("No run data yet. Click **Load latest data** in the sidebar to fetch your Strava activities.")
        return
    df = load_data(_data_version(last_run))
    st.caption(_format_last_sync(last_run, df["start_date"].max()))

    if df.empty:
        st.warning("No training data to display.")
        return

    run_limit = st.sidebar.slider("Number of recent runs", min_value=5, max_value=min(50, len(df)), value=min(10, len(df)))
    recent_df = df.tail(run_limit).copy()

    c1, c2, c3 = st.columns(3)
    c1.metric("Total runs", len(df))
    c2.metric("Total distance", f"{df['distance_km'].sum():.1f} km")
    c3.metric("Average pace", f"{df['pace_min_per_km'].dropna().mean():.2f} min/km")

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.subheader("Distance trend")
        st.line_chart(recent_df.set_index("start_date")["distance_km"])

    with chart_col2:
        st.subheader("Pace trend")
        st.line_chart(recent_df.set_index("start_date")["pace_min_per_km"])

    st.subheader("Weekly distance")
    weekly = recent_df.set_index("start_date").resample("W")["distance_km"].sum().reset_index()
    st.bar_chart(weekly.set_index("start_date")["distance_km"])

    st.subheader("Recent runs")
    st.dataframe(recent_df[["name", "start_date", "distance_km", "duration_minutes", "pace_min_per_km"]].rename(columns={"pace_min_per_km": "pace_min_per_km"}), use_container_width=True)

    st.subheader("AI Recommendations")
    for insight in generate_recommendation(df):
        st.info(insight)

    st.divider()
    st.subheader("💬 Ask Your AI Coach")

    try:
        coach = AIRunningCoach()
        user_question = st.chat_input("Ask me anything about your training...")

        if user_question:
            with st.spinner("Coach is thinking..."):
                response = coach.ask_coach(user_question, df)
            st.chat_message("user").write(user_question)
            st.chat_message("assistant").write(response)
    except ValueError as exc:
        st.warning(f"Azure OpenAI not configured: {str(exc)}")
    except Exception as exc:
        st.error(f"Error contacting AI Coach: {str(exc)}")


if __name__ == "__main__":
    render()
