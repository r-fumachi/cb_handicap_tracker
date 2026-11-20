# cb_handicap_tracker

Track live spread movement for games using the Cloudbet API.

## Run locally (Python 3.11)

On Windows, create a virtual environment with Python 3.11 and install the project
dependencies:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Create `.streamlit/secrets.toml` with your own credentials (this file is ignored
by Git):

```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-supabase-key"
COOKIE_KEY = "a-long-random-secret"
```

Then start the app:

```powershell
.\.venv\Scripts\python.exe -m streamlit run Home.py
```
