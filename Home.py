import uuid
from time import time

import streamlit as st
from streamlit_autorefresh import st_autorefresh

from cloudbet.search import searchSaveGameData
from cloudbet.trackplot import (
    load_tracker_history,
    plot_live_graph,
    update_tracker_data,
)
from commons import get_sportnames_json, parse_time_to_minutes
from database.client import get_user_state, save_user_state
from utils.utils import fetch_event_data


def new_tracker():
    return {
        "panel_id": uuid.uuid4().hex,
        "event_id": None,
        "event_name": None,
        "homeoraway": "home",
        "initial_spread": 0.0,
        "editing": True,
        "data": [],
        "history_loaded": False,
    }


def save_trackers():
    saved_trackers = [
        {
            key: tracker.get(key)
            for key in ("panel_id", "event_id", "event_name", "homeoraway", "initial_spread", "competition")
        }
        for tracker in st.session_state.multi_trackers
        if tracker.get("event_id") is not None
    ]
    save_user_state({"multi_trackers": saved_trackers})


def reset_event_selection(panel_id):
    st.session_state.pop(f"event_{panel_id}", None)


def restore_trackers():
    saved_state = get_user_state()
    saved_trackers = saved_state.get("multi_trackers")

    if saved_trackers is None and saved_state.get("event_id") is not None:
        saved_trackers = [{
            "event_id": saved_state["event_id"],
            "event_name": saved_state.get("event_name"),
            "homeoraway": saved_state.get("homeoraway", "home"),
            "initial_spread": saved_state.get("initial_spread", 0.0),
        }]

    trackers = []
    for saved_tracker in saved_trackers or []:
        tracker = new_tracker()
        tracker.update(saved_tracker)
        tracker["panel_id"] = saved_tracker.get("panel_id") or tracker["panel_id"]
        tracker["editing"] = False
        tracker["data"] = []
        tracker["history_loaded"] = False
        trackers.append(tracker)
    return trackers


st.title("📊 Multi-Event Live Tracker")
st.caption("Add event panels to follow multiple live spreads in one view.")

if "sport_names" not in st.session_state:
    st.session_state.sport_names = get_sportnames_json()
if "multi_trackers" not in st.session_state:
    st.session_state.multi_trackers = restore_trackers()
if "eventData" not in st.session_state:
    st.session_state.eventData, st.session_state.gameData = searchSaveGameData(
        sport="basketball",
        eventName="NCAAM",
    )
if not st.session_state.multi_trackers:
    st.session_state.multi_trackers.append(new_tracker())

st.subheader("Find events")
with st.form("event_search_form"):
    col1, col2 = st.columns(2)
    with col1:
        hours_from = st.number_input("How many hours ago (From)?", min_value=1, value=1)
    with col2:
        hours_to = st.number_input("How many hours ago (To)?", min_value=-100, value=0)

    sport_labels = list(st.session_state.sport_names.values())
    basketball_index = list(st.session_state.sport_names).index("basketball")
    selected_sport_label = st.selectbox(
        "Select Sport",
        sport_labels,
        index=basketball_index,
        key="multi_search_sport",
    )
    search_submitted = st.form_submit_button("🔍 Search Events")

if search_submitted:
    selected_sport = {
        label: key for key, label in st.session_state.sport_names.items()
    }[selected_sport_label]
    current_time = int(time())
    st.session_state.eventData, st.session_state.gameData = searchSaveGameData(
        sport=selected_sport,
        eventName="",
        ts=current_time - hours_from * 3600,
        tf=current_time - hours_to * 3600,
    )
    st.rerun()

st.subheader("Tracked events")
if st.button("➕ Add new event", key="add_tracker"):
    st.session_state.multi_trackers.append(new_tracker())
    st.rerun()

competitions = [competition["name"] for competition in st.session_state.eventData]
active_tracker_count = 0

for index, tracker in enumerate(st.session_state.multi_trackers):
    with st.container(border=True):
        if tracker.get("event_id") is None or tracker.get("editing", False):
            st.markdown("### Choose an event")
            if not competitions:
                st.info("Search for events before selecting one.")
            else:
                competition_default = tracker.get("competition")
                competition_index = (
                    competitions.index(competition_default)
                    if competition_default in competitions
                    else 0
                )
                competition = st.selectbox(
                    "Competition",
                    competitions,
                    index=competition_index,
                    key=f"competition_{tracker['panel_id']}",
                    on_change=reset_event_selection,
                    args=(tracker["panel_id"],),
                )
                selected_events = next(
                    (
                        item["events"]
                        for item in st.session_state.eventData
                        if item["name"] == competition
                    ),
                    [],
                )
                if selected_events:
                    event_ids = [event["id"] for event in selected_events]
                    event_names = {
                        event["id"]: event["name"] for event in selected_events
                    }
                    current_event_id = tracker.get("event_id")
                    event_index = (
                        event_ids.index(current_event_id)
                        if current_event_id in event_ids
                        else 0
                    )

                    with st.form(f"tracker_form_{tracker['panel_id']}"):
                        event_id = st.selectbox(
                            "Game",
                            event_ids,
                            index=event_index,
                            format_func=lambda value: event_names[value],
                            key=f"event_{tracker['panel_id']}",
                        )
                        side = st.radio(
                            "Track odds for",
                            ["home", "away"],
                            index=0 if tracker.get("homeoraway", "home") == "home" else 1,
                            horizontal=True,
                            key=f"side_{tracker['panel_id']}",
                        )
                        initial_spread = st.number_input(
                            "Initial Spread (optional)",
                            value=float(tracker.get("initial_spread") or 0.0),
                            format="%.1f",
                            key=f"initial_spread_{tracker['panel_id']}",
                        )
                        start_tracking = st.form_submit_button(
                            "📈 Track this event"
                        )

                    if start_tracking:
                        if any(
                            other is not tracker
                            and other.get("event_id") == event_id
                            and other.get("homeoraway") == side
                            for other in st.session_state.multi_trackers
                        ):
                            st.warning("That event and side are already being tracked.")
                        else:
                            tracker.update({
                                "event_id": event_id,
                                "event_name": event_names[event_id],
                                "competition": competition,
                                "homeoraway": side,
                                "initial_spread": initial_spread,
                                "editing": False,
                                "history_loaded": False,
                                "data": [],
                                "last_update_time": None,
                            })
                            load_tracker_history(tracker)
                            save_trackers()
                            st.rerun()
                else:
                    st.info("No events are available for this competition.")

            if tracker.get("event_id") is not None:
                if st.button("Cancel", key=f"cancel_edit_{tracker['panel_id']}"):
                    tracker["editing"] = False
                    st.rerun()
            elif st.button("Remove panel", key=f"remove_draft_{tracker['panel_id']}"):
                st.session_state.multi_trackers.pop(index)
                if not st.session_state.multi_trackers:
                    st.session_state.multi_trackers.append(new_tracker())
                st.rerun()
        else:
            active_tracker_count += 1
            st.markdown(
                f"### {tracker['event_name']} — {tracker['homeoraway'].upper()}"
            )
            if not tracker.get("history_loaded"):
                load_tracker_history(tracker)

            event_summary = fetch_event_data(
                event_id=tracker["event_id"],
                event_name=tracker["event_name"],
                homeOrAway=tracker["homeoraway"],
            )
            if event_summary and isinstance(event_summary, dict):
                if event_summary["status"] == "SELECTION_ENABLED":
                    update_tracker_data(tracker, event_summary)
                    if tracker["data"]:
                        st.write("Latest Event Summary:", tracker["data"][-1])
                else:
                    st.caption(f"Handicap market unavailable: {event_summary['status']}")
                    if event_summary["status"] != "Event Over":
                        st.write({
                            "event_id": event_summary["event_id"],
                            "event_name": event_summary["event_name"],
                            "spread": float(event_summary["spread"]),
                            "price": float(event_summary["price"]),
                            "status": event_summary["status"],
                            "marketurl": event_summary["marketUrl"],
                            "homeoraway": tracker["homeoraway"],
                            "time_since_start": parse_time_to_minutes(
                                event_summary["time_since_start"]
                            ),
                        })
            else:
                st.caption("Live event data is not currently available.")

            if tracker["data"]:
                plot_live_graph(
                    tracker["initial_spread"],
                    data=tracker["data"],
                    event_name=tracker["event_name"],
                    homeoraway=tracker["homeoraway"],
                    chart_key=f"spread_{tracker['panel_id']}_{tracker['event_id']}",
                )
            else:
                st.info("Waiting for the first data point.")

            edit_col, remove_col = st.columns(2)
            with edit_col:
                if st.button("✏️ Change event", key=f"edit_{tracker['panel_id']}"):
                    tracker["editing"] = True
                    st.rerun()
            with remove_col:
                if st.button("Remove", key=f"remove_{tracker['panel_id']}"):
                    st.session_state.multi_trackers.pop(index)
                    save_trackers()
                    if not st.session_state.multi_trackers:
                        st.session_state.multi_trackers.append(new_tracker())
                    st.rerun()

if active_tracker_count:
    st_autorefresh(interval=30000, key="multi_tracker_refresh")
