import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

try:
    from .config import (
        CACHE_DIR,
        CACHE_ENABLED,
        CLIENT_ID,
        CLIENT_SECRET,
        STRAVA_ACCESS_TOKEN,
        STRAVA_REFRESH_TOKEN,
    )
except ImportError:  # pragma: no cover
    from config import (
        CACHE_DIR,
        CACHE_ENABLED,
        CLIENT_ID,
        CLIENT_SECRET,
        STRAVA_ACCESS_TOKEN,
        STRAVA_REFRESH_TOKEN,
    )

from .utils import setup_logging


class StravaClient:
    """Small wrapper around the Strava v3 API with token refresh handling."""

    def __init__(
        self,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        logger: Optional[Any] = None,
        cache_enabled: Optional[bool] = None,
    ) -> None:
        self.logger = logger or setup_logging()
        self.access_token = access_token or STRAVA_ACCESS_TOKEN
        self.refresh_token = refresh_token or STRAVA_REFRESH_TOKEN
        self.client_id = client_id or CLIENT_ID
        self.client_secret = client_secret or CLIENT_SECRET
        self.session = requests.Session()
        self._activity_cache: Dict[int, Dict[str, Any]] = {}
        self.cache_enabled = CACHE_ENABLED if cache_enabled is None else cache_enabled
        self.cache_dir = Path(CACHE_DIR)
        if self.cache_enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def clear_cache(cache_dir: Path | None = None) -> None:
        """Remove cached Strava API responses."""
        directory = Path(cache_dir or CACHE_DIR)
        if not directory.exists():
            return
        for cache_file in directory.glob("*.json"):
            cache_file.unlink(missing_ok=True)

    def _set_auth_header(self) -> None:
        if not self.access_token:
            raise ValueError("Missing Strava access token")
        self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})

    def _cache_key(self, endpoint: str, params: Optional[Dict[str, Any]]) -> str:
        cache_input = json.dumps({"endpoint": endpoint, "params": params or {}}, sort_keys=True)
        return hashlib.sha256(cache_input.encode("utf-8")).hexdigest()

    def _cache_path(self, endpoint: str, params: Optional[Dict[str, Any]]) -> Path:
        return self.cache_dir / f"{self._cache_key(endpoint, params)}.json"

    def _load_cache(self, endpoint: str, params: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not self.cache_enabled:
            return None
        cache_file = self._cache_path(endpoint, params)
        if cache_file.exists():
            try:
                return json.loads(cache_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return None
        return None

    def _save_cache(self, endpoint: str, params: Optional[Dict[str, Any]], payload: Any) -> None:
        if not self.cache_enabled:
            return
        cache_file = self._cache_path(endpoint, params)
        cache_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def refresh_access_token(self) -> Dict[str, str]:
        """Refresh expired access tokens using the Strava OAuth endpoint."""
        if not self.client_id or not self.client_secret or not self.refresh_token:
            raise ValueError("Missing Strava OAuth credentials")

        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
        }

        try:
            response = self.session.post(
                "https://www.strava.com/oauth/token",
                data=payload,
                timeout=30,
            )
            response.raise_for_status()
            token_data = response.json()
        except requests.RequestException as exc:
            self.logger.exception("Failed to refresh Strava token: %s", exc)
            raise RuntimeError("Failed to refresh Strava access token") from exc

        self.access_token = token_data.get("access_token", self.access_token)
        self.refresh_token = token_data.get("refresh_token", self.refresh_token)
        os.environ["STRAVA_ACCESS_TOKEN"] = self.access_token
        os.environ["STRAVA_REFRESH_TOKEN"] = self.refresh_token
        try:
            from .auth_helper import update_env_file

            update_env_file(
                {
                    "STRAVA_ACCESS_TOKEN": self.access_token,
                    "STRAVA_REFRESH_TOKEN": self.refresh_token,
                }
            )
        except OSError as exc:
            self.logger.warning("Could not persist refreshed Strava tokens to .env: %s", exc)
        self.logger.info("Strava access token refreshed successfully")
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
        }

    def _request(self, endpoint: str, params: Optional[Dict[str, Any]] = None, retries: int = 1) -> Any:
        """Perform a request to the Strava API with retry logic and optional cache support."""
        self._set_auth_header()
        url = f"https://www.strava.com/api/v3{endpoint}"

        if self.cache_enabled:
            cached_response = self._load_cache(endpoint, params)
            if cached_response is not None:
                self.logger.debug("Loaded cached Strava response for %s", endpoint)
                return cached_response

        try:
            response = self.session.get(url, params=params, timeout=30)
        except requests.Timeout as exc:
            self.logger.warning("Strava request timed out: %s", exc)
            raise RuntimeError("The Strava request timed out") from exc
        except requests.RequestException as exc:
            self.logger.exception("Strava request failed: %s", exc)
            raise RuntimeError("The Strava request failed") from exc

        if response.status_code == 401 and retries > 0:
            self.logger.warning("Access token expired. Refreshing token and retrying")
            self.refresh_access_token()
            return self._request(endpoint, params=params, retries=retries - 1)

        if response.status_code == 429:
            self.logger.warning("Strava API rate limit exceeded")
            raise RuntimeError("Strava API rate limit exceeded")

        if response.status_code >= 400:
            self.logger.error(
                "Strava API error %s for %s: %s",
                response.status_code,
                endpoint,
                response.text,
            )
            raise RuntimeError(
                f"Strava API request failed with status {response.status_code}: {response.text}"
            )

        payload = response.json()
        if self.cache_enabled:
            self._save_cache(endpoint, params, payload)
        return payload

    def get_activities(self, page: int = 1, per_page: int = 30) -> List[Dict[str, Any]]:
        """Fetch one page of activities from Strava."""
        params = {"page": page, "per_page": per_page}
        return self._request("/athlete/activities", params=params)

    def get_activity_details(self, activity_id: int) -> Dict[str, Any]:
        """Fetch details for a single activity, using cache when available."""
        if activity_id in self._activity_cache:
            return self._activity_cache[activity_id]

        details = self._request(f"/activities/{activity_id}")
        self._activity_cache[activity_id] = details
        return details

    def get_all_activities(self, per_page: int = 100, max_pages: int = 5) -> List[Dict[str, Any]]:
        """Iterate through Strava activity pages until the API stops returning results."""
        activities: List[Dict[str, Any]] = []
        page = 1

        while page <= max_pages:
            chunk = self.get_activities(page=page, per_page=per_page)
            if not chunk:
                break
            activities.extend(chunk)
            if len(chunk) < per_page:
                break
            page += 1

        return activities
