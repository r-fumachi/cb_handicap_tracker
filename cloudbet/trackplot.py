import streamlit as st
import pandas as pd
from time import time as current_time
from datetime import datetime, timezone, timedelta
from dateutil.parser import isoparse
from plotly import graph_objects as go
from commons import parse_time_to_minutes
from cloudbet.search import searchSaveGameData
from database.client import init_session_data_from_db, upload_to_storage, db, save_user_state
from database.client import get_event_records

def update_session_data(event_summary):
    event_id = event_summary["event_id"]
    init_session_data_from_db(event_id)

    # 2. Ensure last_update_time exists
    if "last_update_time" not in st.session_state:
        st.session_state.last_update_time = None

    dt_current_time = datetime.now(timezone.utc)
    last_time = None
    if st.session_state.last_update_time:
        last_time = isoparse(st.session_state.last_update_time)
    # 3. Only add new point every 30s
    if last_time and dt_current_time - last_time < timedelta(seconds=30):
        return  # too soon, skip

    record = {
        "event_id": event_summary["event_id"],
        "event_name": event_summary["event_name"],
        "spread": float(event_summary["spread"]),
        "price": float(event_summary["price"]),
        "status": event_summary["status"],
        "marketurl": event_summary["marketUrl"],
        "time_since_start": parse_time_to_minutes(event_summary["time_since_start"]),
        "homeoraway": st.session_state.homeoraway,
    }

    st.session_state.data.append(record)
    resp = db.table("game_records").insert(record).execute()
    # 6. Update last_update_time from DB or from now
    if resp.data:
        created_at = resp.data[0].get("created_at")

        st.session_state.last_update_time = created_at
    else:
        st.session_state.last_update_time = dt_current_time.replace(microsecond=0).isoformat()

def load_tracker_history(tracker):
    tracker["data"] = get_event_records(tracker["event_id"])
    tracker["last_update_time"] = (
        tracker["data"][-1].get("created_at") if tracker["data"] else None
    )
    tracker["history_loaded"] = True


def update_tracker_data(tracker, event_summary):
    current_time = datetime.now(timezone.utc)
    last_update_time = tracker.get("last_update_time")
    if last_update_time and current_time - isoparse(last_update_time) < timedelta(seconds=30):
        return

    record = {
        "event_id": event_summary["event_id"],
        "event_name": event_summary["event_name"],
        "spread": float(event_summary["spread"]),
        "price": float(event_summary["price"]),
        "status": event_summary["status"],
        "marketurl": event_summary["marketUrl"],
        "time_since_start": parse_time_to_minutes(event_summary["time_since_start"]),
        "homeoraway": tracker["homeoraway"],
    }
    response = db.table("game_records").insert(record).execute()
    if response.data:
        record.update(response.data[0])
    else:
        record["created_at"] = current_time.replace(microsecond=0).isoformat()

    tracker["data"].append(record)
    tracker["last_update_time"] = record["created_at"]


def plot_live_graph(
    original_spread,
    gplaceholder=None,
    data=None,
    event_name=None,
    homeoraway=None,
    chart_key=None,
):
    graph_data = st.session_state.get("data", []) if data is None else data
    if len(graph_data) < 1:
        st.warning("Waiting for first data point...")
        return

    df = pd.DataFrame(graph_data)
    event_name = event_name or st.session_state.get("event_name", "")
    homeoraway = homeoraway or st.session_state.get("homeoraway", "")

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
        title=f"Live spread of {event_name} - {homeoraway.upper()}",
        xaxis_title="Time",
        yaxis_title="Spread",
        template="plotly_white",
        showlegend=False,
        uirevision=chart_key or f"{event_name}:{homeoraway}",
    )

    if gplaceholder is not None:
        gplaceholder.plotly_chart(fig, width="stretch")
    else:
        st.plotly_chart(fig, width="stretch", key=chart_key)

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
    st.session_state.ts = int(current_time()) - ts * 3600
    st.session_state.tf = int(current_time()) - tf * 3600

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
    homeoraway = st.radio("Track odds for:", ["home", "away"])

    # --- Initial Spread ---
    initial_spread = st.number_input("Initial Spread (optional)", value=0.0, format="%.1f")

    # --- Start Tracking (Lock Selection) ---
    if st.button("🚀 Start Tracking"):
        st.session_state.event_id = event_options[selected_event_name]
        st.session_state.event_name = selected_event_name
        st.session_state.homeoraway = homeoraway
        st.session_state.initial_spread = initial_spread
        st.session_state.selection_done = True
        st.session_state.tracking_active = True

        tracking_keys = [
            "event_id", "event_name", "homeoraway",
            "initial_spread", "selection_done", "tracking_active", "init_done"
        ]
        payload = {key: st.session_state.get(key) for key in tracking_keys}
        save_user_state(payload)

        st.session_state.redirect_to_live = True

        st.rerun()

def export_event_csv(event_id, bucket_name="cbData", folder_name="gameRecords"):
    # 1. Fetch all DB rows for this event
    response = (
        db.table("game_records")
        .select("*")
        .eq("event_id", event_id)
        .order("created_at", desc=False)
        .execute()
    )

    rows = response.data or []

    if not rows:
        st.warning("No data for this event.")
        return

    # 2. Convert to DataFrame
    df = pd.DataFrame(rows)

    # 3. Create CSV bytes
    csv_bytes = df.to_csv(index=False).encode("utf-8")

    # 4. Setup filename + remote path
    event_name_clean = df["event_name"].iloc[0].replace(" ", "")
    filename = f"{event_name_clean}_{event_id}.csv"
    remote_path = f"{folder_name}/{filename}"

    # 5. Upload CSV to Supabase Storage (overwrites existing)
    upload_to_storage(bucket_name, remote_path, csv_bytes)

    st.success(f"CSV saved to Supabase Storage at {remote_path}")

    # 6. Provide download button for user
    st.download_button(
        label="Download CSV",
        data=csv_bytes,
        file_name=filename,
        mime="text/csv"
    )
