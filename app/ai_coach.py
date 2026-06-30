from __future__ import annotations

from typing import Any, Optional

import pandas as pd
from google import genai
from google.genai import types

try:
    from .config import GEMINI_API_KEY, GEMINI_MODEL, get_setting
except ImportError:  # pragma: no cover
    from config import GEMINI_API_KEY, GEMINI_MODEL, get_setting

from .utils import setup_logging


def _format_number(value: Any, fmt: str, suffix: str = "") -> str:
    """Format a numeric value, returning N/A for missing data."""
    if value is None:
        return "N/A"
    try:
        if pd.isna(value):
            return "N/A"
    except (TypeError, ValueError):
        pass
    return f"{float(value):{fmt}}{suffix}"


class AIRunningCoach:
    """AI coach that provides personalized running advice using Google Gemini."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        logger: Optional[Any] = None,
    ) -> None:
        self.logger = logger or setup_logging()
        self.api_key = api_key or GEMINI_API_KEY or get_setting("GEMINI_API_KEY")
        self.model_name = model or GEMINI_MODEL or get_setting("GEMINI_MODEL", "gemini-2.5-flash")

        if not self.api_key:
            raise ValueError("Gemini API key is missing. Set GEMINI_API_KEY in .env or Streamlit secrets.")

        self.client = genai.Client(api_key=self.api_key)

    def _build_context(self, df: pd.DataFrame) -> str:
        """Build a text summary of activity data for context."""
        if df.empty:
            return "No activity data available."

        df = df.copy()
        df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")

        total_distance = df["distance_km"].sum()
        avg_pace = df["pace_min_per_km"].dropna().mean()
        total_runs = len(df)
        avg_hr = df["average_heartrate"].dropna().mean() if "average_heartrate" in df.columns else None

        weekly = df.set_index("start_date").resample("W")["distance_km"].sum()
        recent_week = weekly.iloc[-1] if len(weekly) > 0 else 0
        prior_week = weekly.iloc[-2] if len(weekly) > 1 else None

        context = f"""
Running Activity Summary:
- Total runs: {total_runs}
- Total distance: {_format_number(total_distance, ".1f", " km")}
- Average pace: {_format_number(avg_pace, ".2f", " min/km")}
- This week: {_format_number(recent_week, ".1f", " km")}
- Last week: {_format_number(prior_week, ".1f", " km")}
- Average heart rate: {_format_number(avg_hr, ".0f", " bpm")}
"""
        return context.strip()

    def ask_coach(self, question: str, activity_df: pd.DataFrame) -> str:
        """Ask the AI coach a question about your training, with activity context."""
        context = self._build_context(activity_df)

        system_message = """You are an experienced running coach with expertise in training plans, performance analysis, and injury prevention.
You provide personalized advice based on the runner's activity data and training history.
Be concise, actionable, and supportive in your responses.
Use the provided activity summary to give context-aware coaching advice."""

        user_message = f"""Here is the runner's activity data:

{context}

Question: {question}

Please provide specific, actionable coaching advice based on this data."""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=system_message,
                    temperature=0.7,
                    max_output_tokens=500,
                ),
            )
            return response.text or "No response generated."
        except Exception as exc:
            self.logger.exception("Failed to get response from Gemini: %s", exc)
            message = str(exc)
            if "429" in message or "RESOURCE_EXHAUSTED" in message:
                raise RuntimeError(
                    "Gemini API quota exceeded for this model. "
                    "Try again later or set GEMINI_MODEL=gemini-2.5-flash in your secrets."
                ) from exc
            if "API key" in message or "API_KEY" in message:
                raise RuntimeError(
                    "Invalid or missing Gemini API key. Set GEMINI_API_KEY in .env or Streamlit secrets."
                ) from exc
            raise RuntimeError(f"Failed to get AI coaching response: {message}") from exc
