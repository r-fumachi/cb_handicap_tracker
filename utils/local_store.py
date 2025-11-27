import json
from os import path, getcwd, remove, makedirs
import streamlit as st

LOCALSTORAGE_DIRPATH = path.join(getcwd(),path.join('cbData','localStorage'))
LOCAL_STATE_FILENAME = "local_state.json"
LOCAL_STATE_PATH = path.join(LOCALSTORAGE_DIRPATH, LOCAL_STATE_FILENAME)

def save_state_json(payload, name: str):
    filepath = path.join(LOCALSTORAGE_DIRPATH, name)
    makedirs(path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(payload, f)

def load_state_json(name):
    filepath = path.join(LOCALSTORAGE_DIRPATH, name)
    if path.exists(filepath):
        with open(filepath, "r") as f:
            data = json.load(f)
            for k,v in data.items():
                st.session_state[k] = v

def delete_state_json(name):
    filepath = path.join(LOCALSTORAGE_DIRPATH, name)
    if path.exists(filepath):
        remove(filepath)
        st.write(f"Deleted previous {name}.json")