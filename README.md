# AI Running Coach

A production-grade Python application that pulls Strava activities, processes the data, generates coaching recommendations, and exposes a Streamlit dashboard.

## Features
- Fetches Strava activities with pagination and token refresh handling
- Optional API response caching for faster development cycles
- Converts raw activity payloads into versioned CSV datasets
- Includes heart rate analysis when available
- Produces coaching insights for training load and performance trends
- Displays a dashboard with metrics, charts, recent runs, and recommendations

## Setup
1. Create and activate a Python virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project root with the required Strava credentials:
   ```env
   STRAVA_ACCESS_TOKEN=your_access_token
   STRAVA_REFRESH_TOKEN=your_refresh_token
   CLIENT_ID=your_client_id
   CLIENT_SECRET=your_client_secret
   ```

## Run the main pipeline
```bash
python -m app.main
```

## Run the dashboard
```bash
streamlit run streamlit_app.py
```

Local alternative:
```bash
streamlit run app/dashboard.py
```

The dashboard requires Google sign-in. Only email addresses listed in `ALLOWED_EMAILS` can access the app.

### Google authentication setup
1. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`.
2. In [Google Cloud Console](https://console.cloud.google.com/apis/credentials), create an OAuth **Web application** client.
3. Add an authorized redirect URI:
   - Local: `http://localhost:8501/oauth2callback`
   - Streamlit Cloud: `https://YOUR-APP.streamlit.app/oauth2callback`
4. On the Google Auth Platform **Audience** page, add each allowed user as a test user (while the app is in Testing), or publish the app when ready.
5. Fill in `.streamlit/secrets.toml`:
   - `ALLOWED_EMAILS` — comma-separated list of Google accounts that may sign in
   - `[auth]` — `client_id`, `client_secret`, `redirect_uri`, and a strong random `cookie_secret`
6. Run the dashboard and sign in with an allowed Google account.

The dashboard loads activities from SQLite on startup. Use **Load latest data** in the sidebar to fetch fresh activities from Strava and refresh the view.

## Deploy on Streamlit Community Cloud
1. Push this repository to GitHub.
2. Open [share.streamlit.io](https://share.streamlit.io) and create a new app from the repo.
3. Set **Main file path** to `streamlit_app.py` (use forward slashes, not `app\dashboard.py`).
4. Add secrets in the app settings (see `.streamlit/secrets.toml.example`), including `[auth]` and `ALLOWED_EMAILS`.
5. In Google Cloud, add your Streamlit app redirect URI: `https://YOUR-APP.streamlit.app/oauth2callback`.
6. Deploy.

**Note:** Cloud hosting uses ephemeral storage, so SQLite data resets on redeploy. Use **Load latest data** after each deploy.

## Authorize Strava
1. Open the authorization URL:
   ```bash
   python -m app.auth_helper auth-url
   ```
2. Authorize the app in your browser and copy the returned `code`.
3. Exchange the code for tokens:
   ```bash
   python -m app.auth_helper exchange YOUR_CODE
   ```
4. The helper will update `.env` with `STRAVA_ACCESS_TOKEN` and `STRAVA_REFRESH_TOKEN`.

## Register your Strava app
1. Visit Strava developers: `https://developers.strava.com/apps`
2. Create or select your application.
3. Set the `Authorization Callback Domain` or redirect URI to `localhost` or the value you use in the helper.
   - Example: `http://localhost`
4. Use the same redirect URI with `python -m app.auth_helper auth-url` and `python -m app.auth_helper exchange`.

## Run tests
```bash
pytest
```

## Run tests
```bash
pytest
```

## Output files
- Activity data is stored in `data/running_coach.db` (SQLite).
- On first run, existing `data/processed_activities_*.csv` files are imported automatically if the database is empty.
- Strava API cache files are stored in `data/cache/`.
- Application logs are written to `logs/app.log`.
