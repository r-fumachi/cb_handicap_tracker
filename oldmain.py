from cloudbet.trackplot import *
from cloudbet.search import searchSaveGameData
import time
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from utils.utils import fetch_event_data

# betData = {
#     "id":31664071,
#     "marketname":"basketball.handicap",
#     "outcome": "home",
#     "params": "handicap=-12.5",
#     "price": 1.86,
# }
#
# placeBet(betData, currency='USDT', stake=1)

#lines = getLines('31664071','basketball.handicap/home?handicap=-14')
# event_data = getCleanEvent(31664118)
# lines = get_handicap_market_details(event_data)

if "event_id" in st.session_state:
    st_autorefresh(interval=30000)

def selectormain():
    # First: Require selection screen before graph
    if "selection_done" not in st.session_state:
        if "eventData" not in st.session_state:
            st.session_state.eventData, st.session_state.gameData = searchSaveGameData(
                sport='basketball',
                eventName='NCAAM'
            )
        time_game_selector()
        st.stop()
    # After selection, proceed to tracking
    event_id = st.session_state.event_id
    event_name = st.session_state.event_name
    homeoraway = st.session_state.homeoraway
    initial_spread = st.session_state.initial_spread

    st.subheader(f"📊 Live Tracking — {event_name} ({homeoraway.upper()})")

    # fetch & track as before
    event_summary = fetch_event_data(event_id, event_name, homeoraway)
    print(event_summary)

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
            }
        else:
            record = event_summary
        if "data" in st.session_state and len(st.session_state.data) > 0:
            st.write(f"Latest Event Summary:\nHANDICAP BET OFF = {event_summary['status']}", record)
            if "graph_placeholder" not in st.session_state:
                st.session_state.graph_placeholder = st.empty()
            plot_live_graph(initial_spread)
        else:
            st.write(f"Latest Event Summary:\nHANDICAP BET OFF = {event_summary['status']}", record)
            st.warning("No valid data yet to plot")
    else:
        update_session_data(event_summary)

        if "data" in st.session_state and len(st.session_state.data) > 0:
            st.write("Latest Event Summary:", st.session_state.data[-1])
            if "graph_placeholder" not in st.session_state:
                st.session_state.graph_placeholder = st.empty()
            plot_live_graph(initial_spread)
        else:
            st.warning("Waiting for first data point...")

    st.query_params["run"] = str(time.time())

# if __name__ == "__main__":
    # searchSaveGameData('basketball','NCAAM', ts=CURRENT_TIME-3600, tf=CURRENT_TIME)
    # main()
    # selectormain()
