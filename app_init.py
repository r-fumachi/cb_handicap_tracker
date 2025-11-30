from os import path, remove
from utils.local_store import LOCAL_STATE_PATH

def initialize_app():
    # Always remove the old flag file when app starts
    if path.exists(LOCAL_STATE_PATH):
        remove(LOCAL_STATE_PATH)
        print("removed local file")