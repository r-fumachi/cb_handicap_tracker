import logging
import streamlit as st
from json import dump, load
from os import path, getcwd
from time import time as current_time
from datetime import timedelta
from streamlit_javascript import st_javascript

dataPath = path.join(getcwd(),'cbData')
CURRENT_TIME: int = int(current_time())

def saveData(data,fileName:str):
    outfilePath = path.join(dataPath,fileName)
    with open(outfilePath, 'w') as outfile:
        dump(data, outfile)

def parse_time_to_minutes(time_str):
    parts = time_str.split(':')
    if len(parts) == 3:
        t = timedelta(hours=int(parts[0]), minutes=int(parts[1]), seconds=float(parts[2]))
        return round(t.total_seconds() / 60, 2)
    return 0

def get_sportnames_json():
    filepath = path.join(dataPath, "sportnames.json")
    with open(filepath) as f:
        sportnames = load(f)
    return sportnames

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def get_user_id():
# If the UID was already obtained, use it
    if "uid" in st.session_state:
        return st.session_state["uid"]

    # Ask JavaScript to return the UID
    uid = st_javascript("""
        (async () => {
            let id = localStorage.getItem('user_id');
            if (!id) {
                id = crypto.randomUUID();
                localStorage.setItem('user_id', id);
            }
            return id;
        })();
    """)

    # Streamlit will return "0" before JavaScript finishes.
    # Ignore that value and wait for correct UID.
    if not uid or uid == 0 or uid == "0":
        st.stop()  # <-- STOP HERE and wait for next rerun

    # Now JS has returned an actual UID
    st.session_state["uid"] = uid
    st.rerun()  # <-- restart app with UID loaded
