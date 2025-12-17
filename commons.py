import logging
import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager
import uuid
from json import dump, load
from os import path, getcwd
from datetime import timedelta

dataPath = path.join(getcwd(),'cbData')
COOKIE_KEY = st.secrets["COOKIE_KEY"]
cookies = EncryptedCookieManager(prefix="cb_handicap", password=COOKIE_KEY)

if not cookies.ready():
    st.stop()

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
    if "uid" in st.session_state:
        return st.session_state["uid"]
    
    uid = cookies.get("user_id")
    if not uid:
        uid = str(uuid.uuid4())
        st.session_state.uid = uid
        cookies["user_id"] = uid
        cookies.save()
    return uid
