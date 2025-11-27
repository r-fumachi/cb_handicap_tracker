import streamlit as st
from postgrest import PostgrestClient
from storage3 import StorageClient
from gotrue import SyncGoTrueClient

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

db = PostgrestClient(
    f"{SUPABASE_URL}/rest/v1",
    headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
)

storage = StorageClient(
    f"{SUPABASE_URL}/storage/v1",
    headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
)

auth = SyncGoTrueClient(
    url=f"{SUPABASE_URL}/auth/v1",
    headers={"apikey": SUPABASE_KEY}
)

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
