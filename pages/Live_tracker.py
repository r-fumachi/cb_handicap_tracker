import streamlit as st
from streamlit_autorefresh import st_autorefresh
from utils.utils import fetch_event_data
from commons import parse_time_to_minutes
from cloudbet.trackplot import update_session_data, plot_live_graph
from utils.local_store import LOCAL_STATE_PATH
from os import path
from json import load

# Load tracking state from file if exists
if path.exists(LOCAL_STATE_PATH):
    with open(LOCAL_STATE_PATH, "r") as f:
        tracking_data = load(f)
        st.session_state.update(tracking_data)
else:
    st.warning("⚠️ No active tracking session. Please select a game first.")
    if st.button("⬅️ Go to Game Selection"):
        st.switch_page("Home.py")
    st.stop()

# Always update last_event_id to current
if "event_id" in st.session_state:
    st.session_state.last_event_id = st.session_state.event_id

st.subheader(f"📊 Live Tracking — {st.session_state.event_name} ({st.session_state.homeOrAway.upper()})")

# Fetch event data
event_summary = fetch_event_data(
    event_id=st.session_state.event_id,
    event_name=st.session_state.event_name,
    homeOrAway=st.session_state.homeOrAway
)
print(event_summary)

# Preserve graph even if selection is disabled
if event_summary:
    if not event_summary["status"] == "SELECTION_ENABLED":
        if event_summary["status"] != "Event Over":
            record = {
                "event_id": event_summary["event_id"],
                "event_name": event_summary["event_name"],
                "spread": float(event_summary["spread"]),
                "price": float(event_summary["price"]),
                "status": event_summary["status"],
                "marketUrl": event_summary["marketUrl"],
                "time_since_start": parse_time_to_minutes(event_summary["time_since_start"]),
                "homeOrAway": st.session_state.homeOrAway,
            }
        else:
            record = event_summary
        if "data" in st.session_state and len(st.session_state.data) > 0:
            st.write(f"Latest Event Summary:\nHANDICAP BET OFF = {event_summary['status']}", record)
            plot_live_graph(st.session_state.initial_spread, st.empty())
        else:
            st.write(f"Latest Event Summary:\nHANDICAP BET OFF = {event_summary['status']}", record)
            st.warning("No valid data yet to plot")
    else:
        update_session_data(event_summary)

        if "data" in st.session_state and len(st.session_state.data) > 0:
            st.write("Latest Event Summary:", st.session_state.data[-1])
            plot_live_graph(st.session_state.initial_spread, st.empty())
        else:
            st.warning("Waiting for first data point...")

if "event_id" in st.session_state:
    st_autorefresh(interval=30000)

# Navigation buttons — do NOT clear data
st.write("---")
col1, col2 = st.columns(2)
with col1:
    if st.button("🔙 Back to Search"):
        st.switch_page("Home.py")
with col2:
    if st.button("🔁 Restart Tracking"):
        for key in ["event_id", "event_name", "homeOrAway", "initial_spread", "tracking_active", "selection_done"]:
            st.session_state.pop(key, None)
        st.switch_page("Home.py")