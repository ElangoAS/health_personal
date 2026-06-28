from __future__ import annotations

import sys
from pathlib import Path
import tempfile

# Add project root to path so imports work with streamlit run
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd
import streamlit as st

from app.recommendations import generate_recommendation
from app.utils import get_latest_csv
from app.ai_coach import AIRunningCoach


st.set_page_config(page_title="AI Running Coach", page_icon="🏃", layout="wide")


@st.cache_data(show_spinner=False)
def load_data(csv_path: str) -> pd.DataFrame:
    """Load a processed CSV file into a DataFrame."""
    df = pd.read_csv(csv_path, parse_dates=["start_date"])
    if "pace_min_per_km" not in df.columns:
        df["pace_min_per_km"] = None
    return df.sort_values("start_date").reset_index(drop=True)


def render() -> None:
    """Render the Streamlit dashboard."""
    st.title("AI Running Coach Dashboard")
    st.caption("Track your training load, pace, and AI coaching insights")

    data_file = st.sidebar.file_uploader("Upload processed CSV", type=["csv"])
    if data_file is not None:
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as temp_file:
            temp_file.write(data_file.getvalue())
            temp_csv_path = Path(temp_file.name)
        df = load_data(str(temp_csv_path))
    else:
        latest_csv = get_latest_csv()
        if latest_csv is None:
            st.info("No processed run data found. Run the main pipeline first to generate data.")
            return
        df = load_data(str(latest_csv))

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
