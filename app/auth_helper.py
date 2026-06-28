from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import requests

from .config import CLIENT_ID, CLIENT_SECRET

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"
OAUTH_AUTHORIZE_URL = "https://www.strava.com/oauth/authorize"
OAUTH_TOKEN_URL = "https://www.strava.com/oauth/token"


def get_authorization_url(
    redirect_uri: str = "http://localhost",
    approval_prompt: str = "force",
    scope: str = "activity:read,activity:read_all",
) -> str:
    """Build a Strava OAuth authorization URL with the required scopes."""
    if not CLIENT_ID:
        raise ValueError("CLIENT_ID must be set in .env before generating the auth URL")

    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "approval_prompt": approval_prompt,
        "scope": scope,
    }
    return f"{OAUTH_AUTHORIZE_URL}?{urlencode(params)}"


def exchange_code_for_tokens(code: str, redirect_uri: str = "http://localhost") -> dict[str, Any]:
    """Exchange a Strava authorization code for access and refresh tokens."""
    if not CLIENT_ID or not CLIENT_SECRET:
        raise ValueError("CLIENT_ID and CLIENT_SECRET must be set in .env before exchanging a code")

    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }

    response = requests.post(OAUTH_TOKEN_URL, data=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def update_env_file(values: dict[str, str], env_file: Path = ENV_FILE) -> None:
    """Update or append values in the .env file."""
    env_file.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    if env_file.exists():
        lines = env_file.read_text(encoding="utf-8").splitlines()

    output_lines: list[str] = []
    existing_keys = {line.split("=", 1)[0]: i for i, line in enumerate(lines) if "=" in line and not line.strip().startswith("#")}

    for line in lines:
        if "=" not in line or line.strip().startswith("#"):
            output_lines.append(line)
            continue
        key, _ = line.split("=", 1)
        if key in values:
            output_lines.append(f"{key}={values[key]}")
        else:
            output_lines.append(line)

    for key, value in values.items():
        if key not in existing_keys:
            output_lines.append(f"{key}={value}")

    env_file.write_text("\n".join(output_lines).strip() + "\n", encoding="utf-8")


def main() -> None:
    """CLI entrypoint for generating auth URLs and exchanging codes."""
    parser = argparse.ArgumentParser(description="Strava OAuth helper for the AI Running Coach app")
    subparsers = parser.add_subparsers(dest="command", required=True)

    auth_parser = subparsers.add_parser("auth-url", help="Print the Strava authorization URL")
    auth_parser.add_argument("--redirect-uri", default="http://localhost", help="Redirect URI registered with Strava")

    exchange_parser = subparsers.add_parser("exchange", help="Exchange a Strava code for tokens")
    exchange_parser.add_argument("code", help="Authorization code returned by Strava")
    exchange_parser.add_argument("--redirect-uri", default="http://localhost", help="Redirect URI registered with Strava")

    args = parser.parse_args()

    if args.command == "auth-url":
        url = get_authorization_url(redirect_uri=args.redirect_uri)
        print("Open this URL in your browser and authorize the app:")
        print(url)
    elif args.command == "exchange":
        token_data = exchange_code_for_tokens(code=args.code, redirect_uri=args.redirect_uri)
        print("Token exchange successful. Writing new tokens to .env")
        update_env_file(
            {
                "STRAVA_ACCESS_TOKEN": token_data.get("access_token", ""),
                "STRAVA_REFRESH_TOKEN": token_data.get("refresh_token", ""),
            }
        )
        print(json.dumps(token_data, indent=2))


if __name__ == "__main__":
    main()
