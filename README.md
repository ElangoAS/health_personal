# AI Running Coach

A personal running analytics dashboard that syncs activities from Strava, visualizes training trends, generates rule-based coaching insights, and provides an AI coach powered by Google Gemini.

Access is restricted with **Google sign-in** and an email allowlist, so only approved users can open the app.

---

## Features

| Area | What it does |
|------|----------------|
| **Strava sync** | Fetches run activities with pagination and automatic token refresh |
| **Data storage** | Persists activities in SQLite for fast dashboard loading |
| **Training dashboard** | Metrics, distance/pace charts, weekly volume, and recent runs table |
| **Recommendations** | Rule-based insights for training load, pace, and heart rate trends |
| **AI Coach** | Chat with Gemini Flash about your training (dedicated mobile-friendly tab) |
| **Access control** | Google OAuth login with `ALLOWED_EMAILS` allowlist |
| **Caching** | Optional Strava API response cache for local development |

---

## Project structure

```
health_repo/
├── streamlit_app.py          # Streamlit Cloud entry point
├── app/
│   ├── dashboard.py          # Streamlit UI
│   ├── pipeline.py           # Strava fetch → process → SQLite
│   ├── strava_client.py      # Strava API client
│   ├── data_processor.py     # Activity normalization
│   ├── db.py                 # SQLite persistence
│   ├── recommendations.py  # Rule-based coaching insights
│   ├── ai_coach.py           # Gemini-powered chat coach
│   ├── google_auth.py        # Google login gate
│   ├── auth_helper.py        # Strava OAuth CLI helper
│   └── config.py             # Environment and secrets loading
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.example  # Template for local / Cloud secrets
├── data/                     # SQLite DB and cache (gitignored)
├── logs/                     # Application logs (gitignored)
└── tests/
```

---

## Prerequisites

- Python 3.9+
- A [Strava API application](https://developers.strava.com/apps)
- A [Google Cloud OAuth Web application](https://console.cloud.google.com/apis/credentials) (for dashboard login)
- A [Google AI Studio API key](https://aistudio.google.com/apikey) (for the AI coach)

---

## Quick start (local)

### 1. Clone and install

```bash
git clone <your-repo-url>
cd health_repo
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy the example file and fill in your values:

```bash
copy .env.example .env          # Windows
# cp .env.example .env          # macOS / Linux
```

Required in `.env`:

```env
STRAVA_ACCESS_TOKEN=...
STRAVA_REFRESH_TOKEN=...
CLIENT_ID=...
CLIENT_SECRET=...
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.0-flash
ALLOWED_EMAILS=you@gmail.com
```

### 3. Configure Streamlit secrets (Google login)

```bash
copy .streamlit\secrets.toml.example .streamlit\secrets.toml
```

Edit `.streamlit/secrets.toml` with your Strava tokens, Gemini key, `ALLOWED_EMAILS`, and the `[auth]` block (see [Google authentication](#google-authentication) below).

> **Never commit** `.env` or `.streamlit/secrets.toml` — both are listed in `.gitignore`.

### 4. Run the dashboard

```bash
streamlit run streamlit_app.py
```

Open `http://localhost:8501`, sign in with Google, then click **Load latest data** in the sidebar to sync from Strava.

---

## Dashboard usage

The dashboard has two tabs:

- **Training** — metrics, charts, recent runs, and automated recommendations
- **AI Coach** — chat with Gemini about your training; includes quick-question shortcuts for mobile

**Sidebar controls:**

- **Load latest data** — fetch fresh activities from Strava and refresh the view
- **Number of recent runs** — adjust the chart and table window
- **Log out** — end your Google session

---

## Strava setup

### Register your Strava app

1. Go to [Strava Developers](https://developers.strava.com/apps) and create an application.
2. Set the **Authorization Callback Domain** to `localhost` (or your redirect host).
3. Note your **Client ID** and **Client Secret**.

### Authorize and get tokens

```bash
python -m app.auth_helper auth-url
```

Open the printed URL in your browser, authorize the app, and copy the `code` from the redirect URL.

```bash
python -m app.auth_helper exchange YOUR_CODE
```

This writes `STRAVA_ACCESS_TOKEN` and `STRAVA_REFRESH_TOKEN` to `.env`.

### Run the pipeline (CLI)

```bash
python -m app.main
```

Fetches activities from Strava and stores them in `data/running_coach.db`.

---

## Google authentication

The dashboard uses Streamlit's built-in Google OIDC login. Only emails listed in `ALLOWED_EMAILS` can access the app after signing in.

### Google Cloud setup

1. Open [Google Cloud Console](https://console.cloud.google.com/) and create or select a project.
2. Go to **Google Auth Platform → Clients** and create an OAuth client:
   - Type: **Web application**
   - Authorized redirect URI (local): `http://localhost:8501/oauth2callback`
3. On **Audience**, add your Gmail as a **test user** (while the app is in Testing mode).
4. Copy the **Client ID** and **Client secret**.

### Secrets configuration

Add to `.streamlit/secrets.toml` (local) or **Streamlit Cloud → Settings → Secrets**:

```toml
ALLOWED_EMAILS = "you@gmail.com"

[auth]
redirect_uri = "http://localhost:8501/oauth2callback"
cookie_secret = "a-long-random-string"
client_id = "YOUR-ID.apps.googleusercontent.com"
client_secret = "GOCSPX-..."
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

| Setting | Source |
|---------|--------|
| `ALLOWED_EMAILS` | Emails you want to allow |
| `client_id` / `client_secret` | Google Cloud OAuth client |
| `redirect_uri` | Must match Google Console exactly |
| `cookie_secret` | Any long random string you generate |
| `server_metadata_url` | Use the value above (do not change) |

---

## Gemini AI coach

The AI coach uses Google's Gemini Flash model via the `google-genai` SDK.

```env
GEMINI_API_KEY=your_api_key
GEMINI_MODEL=gemini-2.0-flash
```

Get an API key from [Google AI Studio](https://aistudio.google.com/apikey).

---

## Deploy on Streamlit Community Cloud

1. Push the repository to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and click **Create app**.
3. Select your repo and branch (`main`).
4. Set **Main file path** to `streamlit_app.py` (forward slashes only — never `app\dashboard.py`).
5. Open **Settings → Secrets** and paste your full TOML from `secrets.toml.example`, including:
   - Strava credentials
   - `GEMINI_API_KEY` and `GEMINI_MODEL`
   - `ALLOWED_EMAILS`
   - `[auth]` block with Cloud `redirect_uri`:
     ```
     https://YOUR-APP.streamlit.app/oauth2callback
     ```
6. In Google Cloud, add the same Cloud redirect URI under **Clients → Authorized redirect URIs**.
7. Deploy and reboot the app.

> **Note:** Streamlit Cloud uses ephemeral storage. SQLite data resets on redeploy — click **Load latest data** after each deploy.

### Changing the main file path

The main file path can only be set when creating a new app. To change it later, delete and redeploy with `streamlit_app.py`.

---

## Configuration reference

| Variable | Required | Description |
|----------|----------|-------------|
| `STRAVA_ACCESS_TOKEN` | Yes | Strava OAuth access token |
| `STRAVA_REFRESH_TOKEN` | Yes | Strava OAuth refresh token |
| `CLIENT_ID` | Yes | Strava application client ID |
| `CLIENT_SECRET` | Yes | Strava application client secret |
| `GEMINI_API_KEY` | Yes (for AI coach) | Google AI Studio API key |
| `GEMINI_MODEL` | No | Default: `gemini-2.0-flash` |
| `ALLOWED_EMAILS` | Yes (dashboard) | Comma-separated allowed Google accounts |
| `CACHE_ENABLED` | No | Enable Strava API cache locally (`true` / `false`) |
| `[auth]` section | Yes (dashboard) | Google OAuth settings for Streamlit login |

---

## Data and logs

| Path | Purpose |
|------|---------|
| `data/running_coach.db` | SQLite database with processed activities |
| `data/cache/` | Strava API response cache (when enabled) |
| `logs/app.log` | Application log file |

On first run, if the database is empty, any existing `data/processed_activities_*.csv` files are imported automatically.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `app\dashboard.py does not exist` on Cloud | Set main file to `streamlit_app.py` (forward slashes) |
| Google auth not configured on Cloud | Paste secrets in **Settings → Secrets** — local `secrets.toml` is not deployed |
| Access denied after Google login | Add your email to `ALLOWED_EMAILS` and Google test users |
| `redirect_uri_mismatch` | Ensure `redirect_uri` matches Google Console exactly |
| Gemini not configured | Set `GEMINI_API_KEY` in `.env` or Streamlit secrets |
| No run data on dashboard | Click **Load latest data** in the sidebar |

---

## Run tests

```bash
pytest
```

---

## License

Private / personal use. Update this section if you add a license file.
