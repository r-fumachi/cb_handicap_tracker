import streamlit as st
import requests
from postgrest import SyncPostgrestClient
from commons import get_user_id, logger
from typing import Dict

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

db = SyncPostgrestClient(
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

def get_user_state() -> Dict:
    uid = get_user_id()
    logger.info(uid)
    res = (
        db
        .table("user_tracking_state")
        .select("state_json")
        .eq("user_id", uid)
        .maybe_single()
        .execute()
        )
    if res and res.data and res.data.get("state_json"):        
        logger.info("Loaded user session state")
        logger.info(res.data)
        return res.data.get("state_json")
    else:
        return {}
    
def save_user_state(payload):
    uid = get_user_id()
    res = (
        db
        .table("user_tracking_state")
        .upsert({
            "user_id": uid,
            "state_json": payload})
        .execute()
        )
    logger.info("Saved user session state")
    logger.info(res)
    return res

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
