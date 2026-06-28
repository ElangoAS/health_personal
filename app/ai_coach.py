from __future__ import annotations

import json
from typing import Any, Optional

import pandas as pd
from openai import AzureOpenAI

try:
    from .config import OPENAI_API_KEY, OPENAI_DEPLOYMENT_NAME, OPENAI_ENDPOINT, get_setting
except ImportError:  # pragma: no cover
    from config import OPENAI_API_KEY, OPENAI_DEPLOYMENT_NAME, OPENAI_ENDPOINT, get_setting

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
    """AI coach that provides personalized running advice using Azure OpenAI."""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        deployment_name: Optional[str] = None,
        api_key: Optional[str] = None,
        api_version: str = "2024-08-01-preview",
        logger: Optional[Any] = None,
    ) -> None:
        self.logger = logger or setup_logging()
        self.endpoint = endpoint or OPENAI_ENDPOINT or get_setting("OPENAI_ENDPOINT")
        self.deployment_name = deployment_name or OPENAI_DEPLOYMENT_NAME or get_setting("OPENAI_DEPLOYMENT_NAME")
        self.api_key = api_key or OPENAI_API_KEY or get_setting("OPENAI_API_KEY")
        self.api_version = api_version

        if not all([self.endpoint, self.deployment_name, self.api_key]):
            raise ValueError("Azure OpenAI credentials are missing. Check .env for OPENAI_ENDPOINT, OPENAI_DEPLOYMENT_NAME, OPENAI_API_KEY")

        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.endpoint,
        )

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
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.7,
                max_tokens=500,
            )
            return response.choices[0].message.content or "No response generated."
        except Exception as exc:
            self.logger.exception("Failed to get response from Azure OpenAI: %s", exc)
            raise RuntimeError(f"Failed to get AI coaching response: {str(exc)}") from exc
