import streamlit as st
from cloudbet.search import searchSaveGameData
from cloudbet.trackplot import time_game_selector
from app_init import initialize_app
from commons import get_sportnames_json

if "init_done" not in st.session_state:
    initialize_app()
    # Initialize shared session_state keys
    for key in ["event_id", "event_name", "homeOrAway", "initial_spread",
                "ts", "tf", "selection_done"]:
        st.session_state.setdefault(key, None)
    st.session_state.init_done = True

# If tracking already active, show "Go to Live Tracker" button
if st.session_state.get("tracking_active", False):
    if st.button("Go to Live Tracker"):
        st.switch_page("pages/Live_tracker.py")

if "sport_names" not in st.session_state:
    st.session_state.sport_names = get_sportnames_json()

# Run search only on first visit
if "eventData" not in st.session_state:
    st.session_state.eventData, st.session_state.gameData = searchSaveGameData(
        sport='basketball',
        eventName='NCAAM'
    )

time_game_selector()

# When selection_done=True, redirect to Live Tracking page
if st.session_state.get("redirect_to_live", False):
    st.session_state.redirect_to_live = False  # turn it off immediately
    st.switch_page("pages/Live_tracker.py")