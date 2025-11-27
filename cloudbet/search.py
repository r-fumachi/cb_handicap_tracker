from cloudbet.process import processSportData
from commons import saveData, CURRENT_TIME

def searchSaveGameData(sport, eventName, ts=CURRENT_TIME - 3600, tf=CURRENT_TIME):
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
