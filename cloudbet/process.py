from .api import *
from commons import *
from datetime import datetime, timezone
from json import load

def getCleanEvent(eventId):
    eventData = getEvent(eventId)
    allMarketInfo = []
    for market in eventData['markets']:
        submarkets = eventData['markets'][market]['submarkets']

        for submarketName in submarkets.keys():
            selections = eventData['markets'][market]['submarkets'][submarketName]['selections']
            marketInfo = {
                'marketName': market,
                'submarketName': submarketName,
                'selections':selections,
            }
            allMarketInfo.append(marketInfo)

    return {
        'cutoffTime': str(datetime.strptime(eventData['cutoffTime'],"%Y-%m-%dT%H:%M:%SZ")),
        'marketsAmount': len(allMarketInfo),
        'markets': allMarketInfo,
    }

def getCleanUpcomingEvents(**kwargs):
    rawdata = getUpcomingEvents(**kwargs)
    cleanedData = [
        {
            'name':x['name'],
            'events': [
                {
                    'id':game['id'],
                    'name':game['name'],
                    'cutoffTime': game['cutoffTime'],
                }
                for game in x['events']]
        } for x in rawdata]
    print(f"{kwargs.get('sport')} Events: {len(cleanedData)}")
    return cleanedData

def searchSportEvents(sports: List[str],**kwargs):
    allEventData = []
    for sport in sports:
        eventsData = getCleanUpcomingEvents(
            sport=sport, **kwargs)
        allEventData.append(
            {
                'Events Amount': len(eventsData),
                sport:eventsData,
            }
        )
    saveData(allEventData, 'sportEventSearchResults.json')

def processSportData(eventName='',**kwargs):
    allEvents = getCleanUpcomingEvents(**kwargs)
    gameData = []
    for e in range(len(allEvents)):
        if eventName == allEvents[e]['name']:
            allGames = allEvents[e]['events']
            gameData = [
                {
                    'id':x['id'],
                    'name':x['name'],
                    'data': getCleanEvent(x['id'])
                } for x in allGames]

            break
    print(f"Games: {len(gameData)}")
    return allEvents,gameData

def saveBet(betData, currency, stake):
    res = placeBet(betData, currency, stake)
    saveData(res, 'bets.json')

def getMaticBalance():
    #getAccountCurrencies()['currencies'][0] = MATIC
    return getAccountBalance('MATIC')

def getPreviousBets():
    return getBetHistory()['bets']

def searchSportNames(queryString):
    filePath = path.join(getcwd(), 'cloudbet', 'sportnames.json')
    f = open(filePath)
    sportNames = load(f)
    f.close()
    return [k for k, v in sportNames.items() if queryString.lower() in k.lower()]

def getEsportsNames():
    esportList = searchSportNames('esport')
    esportList.extend(['dota_2','hearthstone','heroes_of_the_storm','league_of_legends','overwatch','rocket_league','rainbow_six','starcraft','street_fighter_v','wild_rift'])
    return esportList

def get_handicap_market_details(feed_response):
    handicap_details = []

    event_start_time = feed_response.get("cutoffTime")
    count = 0  # Counter to limit to first 2 entries per event

    for market in feed_response["markets"]:
        if market.get("marketName") == "basketball.handicap":
            for selection in market.get("selections", []):
                handicap_details.append({
                    "cutoffTime": event_start_time,
                    "outcome": selection.get("outcome"),
                    "params": selection.get("params"),
                    "marketUrl": selection.get("marketUrl"),
                    "spread": selection.get("params").split("=")[1],
                    "price": selection.get("price"),
                    "status": selection.get("status")
                })
                count += 1
                if count >= 2:  # Stop after 2 selections
                    break
        if count >= 2:
            break

    return handicap_details

def extract_event_summary(handicap_details, event_name:str, event_id:int, homeOrAway:str):
    try:
        first_entry = handicap_details[0] if homeOrAway.lower() == "home" else handicap_details[1]
    except IndexError as e:
        print(f"Handicap market details are empty. Returning empty list: {handicap_details}")
        return handicap_details

    spread = float(first_entry["spread"])
    cutoffTime_utc = datetime.strptime(first_entry["cutoffTime"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)

    time_elapsed = datetime.now(timezone.utc) - cutoffTime_utc

    return {
        "event_id": event_id,
        "event_name": event_name,
        "event_start_time": first_entry["cutoffTime"],
        "time_since_start": str(time_elapsed),
        "spread": spread if homeOrAway=="home" else spread*-1,
        "price": first_entry["price"],
        "status": first_entry["status"],
        "marketUrl": first_entry["marketUrl"]
    }


