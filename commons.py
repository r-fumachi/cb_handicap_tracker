from json import dump, load
from os import path, getcwd
from time import time as current_time
from datetime import timedelta

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