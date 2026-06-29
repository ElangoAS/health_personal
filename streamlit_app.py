"""Streamlit Community Cloud entry point."""

from __future__ import annotations

import os


def _load_streamlit_secrets() -> None:
    """Map Streamlit Cloud secrets into environment variables before app imports."""
    try:
        import streamlit as st

        for key, value in st.secrets.items():
            if isinstance(value, (str, int, float, bool)):
                os.environ.setdefault(str(key), str(value))
    except Exception:
        return


_load_streamlit_secrets()

from app.dashboard import render

render()
