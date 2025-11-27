import streamlit as st
from supabase import create_client

# Initialize Supabase
supabaseclient = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

def init_session_data_from_db(event_id: int):
    if "data" in st.session_state:
        return

    resp = (
        supabase
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
