from __future__ import annotations

import streamlit as st

from app.config import ALLOWED_EMAILS, is_google_auth_configured


def normalize_email(email: str | None) -> str:
    """Return a lowercase email string for comparisons."""
    return (email or "").strip().lower()


def is_email_allowed(email: str | None, allowed_emails: list[str] | None = None) -> bool:
    """Return True when the email is on the configured allowlist."""
    normalized = normalize_email(email)
    if not normalized:
        return False

    allowlist = allowed_emails if allowed_emails is not None else ALLOWED_EMAILS
    allowed = {normalize_email(item) for item in allowlist if normalize_email(item)}
    if not allowed:
        return False
    return normalized in allowed


def _login_screen() -> None:
    st.title("AI Running Coach")
    st.header("Sign in required")
    st.write("This app is private. Sign in with your Google account to continue.")
    st.button("Log in with Google", on_click=st.login, type="primary")


def _access_denied_screen(email: str | None) -> None:
    st.title("Access denied")
    display_email = email or "unknown"
    st.error(f"Your account ({display_email}) is not authorized to use this app.")
    st.caption("Contact the app owner if you believe this is a mistake.")
    st.button("Log out", on_click=st.logout)


def require_google_auth() -> bool:
    """Gate the dashboard behind Google login and an email allowlist.

    Returns True when the current user may access the app. Calls st.stop()
    when authentication is required but not satisfied.
    """
    if not is_google_auth_configured():
        st.error(
            "Google authentication is not configured. "
            "Add an `[auth]` section to `.streamlit/secrets.toml` (see `.streamlit/secrets.toml.example`)."
        )
        st.stop()
        return False

    if not ALLOWED_EMAILS:
        st.error(
            "No authorized users are configured. "
            "Set `ALLOWED_EMAILS` in `.streamlit/secrets.toml` or your environment."
        )
        st.stop()
        return False

    if not st.user.is_logged_in:
        _login_screen()
        st.stop()
        return False

    email = getattr(st.user, "email", None)
    if not is_email_allowed(email):
        _access_denied_screen(email)
        st.stop()
        return False

    return True


def render_auth_sidebar() -> None:
    """Show the signed-in user and a logout control in the sidebar."""
    name = getattr(st.user, "name", None) or getattr(st.user, "email", "User")
    st.sidebar.caption(f"Signed in as {name}")
    if st.sidebar.button("Log out", use_container_width=True):
        st.logout()
