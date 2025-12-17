from cloudbet.process import processSportData
from commons import saveData
from time import time as current_time


def searchSaveGameData(sport, eventName, ts=current_time() - 3600, tf=current_time()):
    eventData, gameData = processSportData(
        sport=sport,
        eventName=eventName,
        From=ts,
        to=tf,
    )

    saveData(eventData, 'allEvents.json')
    saveData(gameData, 'gameData.json')

    return eventData, gameData

# sportList = ['basketball']
# searchSportEvents(sports=sportList,
#                   From=CURRENT_TIME,
#                   to=CURRENT_TIME + 36000)
#
