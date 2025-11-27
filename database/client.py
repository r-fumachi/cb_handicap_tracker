import streamlit as st
import requests
from postgrest import PostgrestClient
from storage3 import StorageClient
from supabase_auth import SupabaseAuth

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]


auth = SupabaseAuth(
    url=f"{SUPABASE_URL}/auth/v1",
    headers={
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }
)

db = PostgrestClient(
    f"{SUPABASE_URL}/rest/v1",
    headers={
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    },
)

def upload_to_storage(bucket: str, path: str, file_bytes: bytes):
    url = f"{SUPABASE_URL}/storage/v1/object/{bucket}/{path}"

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "text/csv",
        "x-upsert": "true",
    }

    res = requests.post(url, headers=headers, data=file_bytes)
    res.raise_for_status()
    return res.json() if res.text else True

def download_from_storage(bucket: str, path: str) -> bytes | None:
    url = f"{SUPABASE_URL}/storage/v1/object/{bucket}/{path}"

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }

    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        return res.content
    return None

def init_session_data_from_db(event_id: int):
    if "data" in st.session_state:
        return

    resp = (
        db
        .table("game_records")
        .select("*")
        .eq("event_id", event_id)
        .order("created_at", desc=False)
        .execute()
    )

    rows = resp.data or []

    if rows:
        rows_sorted = sorted(rows, key=lambda r: r["created_at"])
        st.session_state.data = rows_sorted
        st.session_state.last_update_time = rows_sorted[-1]["created_at"]
    else:
        st.session_state.data = []
        st.session_state.last_update_time = None
