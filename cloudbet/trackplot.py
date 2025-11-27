import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
from plotly import graph_objects as go
from os import path, getcwd
from commons import parse_time_to_minutes, CURRENT_TIME
from cloudbet.search import searchSaveGameData
from utils.local_store import save_state_json, delete_state_json, LOCAL_STATE_FILENAME

recordspath = path.join(getcwd(),path.join('cbData','gameRecords'))

def update_session_data(event_summary):
    csv_file = event_summary["event_name"].replace(" ","") + str(event_summary["event_id"]) + ".csv"
    csv_path = path.join(recordspath, csv_file)
    if "data" not in st.session_state:
        if path.exists(csv_path):
            st.session_state.data = pd.read_csv(csv_path).to_dict('records')
        else:
            st.session_state.data = []
    if "last_update_time" not in st.session_state:
        st.session_state.last_update_time = None

    current_time = datetime.now(timezone.utc)

    # Convert stored string to datetime
    if st.session_state.last_update_time:
        last_time = datetime.fromisoformat(st.session_state.last_update_time)
    else:
        last_time = None

    # Add new point only after 30 seconds
    if (last_time is None or current_time - last_time >= timedelta(seconds=30)):

        record = {
            "event_id": event_summary["event_id"],
            "event_name": event_summary["event_name"],
            "spread": float(event_summary["spread"]),
            "price": float(event_summary["price"]),
            "status": event_summary["status"],
            "marketUrl": event_summary["marketUrl"],
            "time_since_start": parse_time_to_minutes(event_summary["time_since_start"]),
        }

        st.session_state.data.append(record)
        st.session_state.last_update_time = current_time.isoformat()
        df = pd.DataFrame([record])
        df.to_csv(
            csv_path,
            mode='a',
            index=False,
            header=not path.exists(csv_path)
        )

def plot_live_graph(original_spread, gplaceholder):
    if "data" not in st.session_state or len(st.session_state.data) < 1:
        st.warning("Waiting for first data point...")
        return

    df = pd.DataFrame(st.session_state.data)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["time_since_start"],
        y=df["spread"],
        mode='lines+markers',
        name='Live Spread',
        customdata=df[["price", "status"]],  # Pass extra data
        hovertemplate=(
            "<b>Time:</b> %{x}<br>"
            "<b>Spread:</b> %{y}<br>"
            "<b>Price:</b> %{customdata[0]}<br>"
            "<extra></extra>"
        )
    ))

    # Use original_spread instead of first df value

    fig.add_trace(go.Scatter(
        x=[df["time_since_start"].iloc[0], df["time_since_start"].iloc[-1]],
        y=[original_spread, original_spread],
        mode="lines",
        name="Initial Spread",
        line=dict(dash="dash", color="yellow"),
        hovertemplate="<b>Initial Spread:</b> %{y}<extra></extra>"
    ))

    fig.update_layout(
        title=f"Live spread of {st.session_state.event_name} - {st.session_state.homeOrAway.upper()}",
        xaxis_title="Time",
        yaxis_title="Spread",
        template="plotly_white",
        showlegend=False
    )

    # Use the persistent placeholder instead of re-rendering the container
    gplaceholder.plotly_chart(fig, width='stretch')

def time_game_selector():
    st.title("🎯 Select Game to Track")

    # --- Time Selection Fields ---
    st.subheader("⏳ Search Time Window")
    col1, col2 = st.columns(2)
    with col1:
        ts = st.number_input("How many hours ago (From)?", min_value=1, value=1)
    with col2:
        tf = st.number_input("How many hours ago (To)?", min_value=-100, value=0)

    # Convert hours to timestamps
    st.session_state.ts = CURRENT_TIME - ts * 3600
    st.session_state.tf = CURRENT_TIME - tf * 3600

    # Sport Name
    selected_sport_label = st.selectbox(
        "Select Sport",
        list(st.session_state.sport_names.values()),
        index = list(st.session_state.sport_names).index("basketball"),
    )
    selected_sport = {v: k for k, v in st.session_state.sport_names.items()}[selected_sport_label]

    # --- Competition Dropdown ---
    competitions = [comp["name"] for comp in st.session_state.eventData]
    selected_competition = st.selectbox("Select Competition", competitions)

    # --- Search Again Button (Load New Event Data) ---
    if st.button("🔍 Search Again"):
        eventData, gameData = searchSaveGameData(
            sport=selected_sport,
            eventName=selected_competition,
            ts=st.session_state.ts,
            tf=st.session_state.tf
        )
        st.session_state.eventData = eventData
        st.session_state.gameData = gameData
        st.success("🔄 Event list updated!")
        st.rerun()

    # Filter events matching selected competition
    selected_events = next(
        (comp["events"] for comp in st.session_state.eventData if comp["name"] == selected_competition),
        []
    )

    # --- Event Dropdown ---
    event_options = {event["name"]: event["id"] for event in selected_events}
    selected_event_name = st.selectbox("Select Game", list(event_options.keys()))

    # --- Home/Away Selection ---
    homeOrAway = st.radio("Track odds for:", ["home", "away"])

    # --- Initial Spread ---
    initial_spread = st.number_input("Initial Spread (optional)", value=0.0, format="%.1f")

    # --- Start Tracking (Lock Selection) ---
    if st.button("🚀 Start Tracking"):
        delete_state_json("local_state")
        st.session_state.event_id = event_options[selected_event_name]
        st.session_state.event_name = selected_event_name
        st.session_state.homeOrAway = homeOrAway
        st.session_state.initial_spread = initial_spread
        st.session_state.selection_done = True
        st.session_state.tracking_active = True

        tracking_keys = [
            "event_id", "event_name", "homeOrAway",
            "initial_spread", "selection_done", "tracking_active", "init_done"
        ]
        payload = {key: st.session_state.get(key) for key in tracking_keys}
        save_state_json(payload, LOCAL_STATE_FILENAME)
        print("Saved file")

        st.session_state.redirect_to_live = True

        st.rerun()