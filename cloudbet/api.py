import uuid
import requests
from time import sleep
from typing import Optional, Union, Dict, List, Any
from os import getenv

key = getenv("CLOUDBET_KEY")
baseUrl = 'https://sports-api.cloudbet.com/pub/'

headers = {
    'Content-Type': 'application/json',
    "X-API-Key": key
}


def cbGet(url: str, params: Optional[Dict] = None, retries: int = 3, delay: int = 5) -> Union[Dict, Any]:
    if params is None:
        params = {}

    for attempt in range(1, retries + 1):
        try:
            res = requests.get(baseUrl + url, headers=headers, params=params, timeout=10)
            res.raise_for_status()
            return res.json()

        except (requests.exceptions.ConnectionError,
                requests.exceptions.Timeout) as e:

            print(f"Network error on attempt {attempt}/{retries}: {e}")

            if attempt < retries:
                print(f"Retrying in {delay} seconds...")
                sleep(delay)
            else:
                print("Max retries exceeded. Raising exception.")
                raise

        except requests.exceptions.HTTPError as e:
            print(f"HTTP error (not retryable): {e}")
            raise

    return None


def cbPost(url: str, payload:Optional[Dict]={}) -> Union[Dict,Any]:
    res = requests.post(baseUrl + url, headers=headers, json=payload)
    return res.json()

def getAccountCurrencies():
    return cbGet('v1/account/currencies')

def getAccountBalance(currency):
    return cbGet(f'v1/account/currencies/{currency}/balance')

def getAccountInfo():
    return cbGet('v1/account/info')

def getRawEvents(**kwargs):
    '''
    Required params: 'sport', and either 'live' OR 'from' + 'to'
    '''
    data = {k.lower(): v for k, v in kwargs.items()}
    return cbGet('v2/odds/events', data)

def getUpcomingEvents(**kwargs):
    return getRawEvents(**kwargs)['competitions']

def getEvent(eventId):
    return cbGet(f'v2/odds/events/{eventId}')

def placeBet(betData, currency, stake):
    #Ref https://www.cloudbet.com/api/?urls.primaryName=Trading#/Trading/PlaceBet
    payload = {
        "eventId": str(betData['id']),
        "marketUrl": betData['marketName'] + "/" + betData["outcome"] + "?" + betData["params"],
        "currency": currency,
        "price": str(betData["price"]),
        "stake": str(stake),
        "referenceId": str(uuid.uuid4()),
    }
    res = cbPost('v3/bets/place',payload)
    return {
        'betPayload': payload,
        'response': res,
    }

def getLines(eventId:str,marketUrl:str):
    payload = {
        "eventId": eventId,
        "marketUrl": marketUrl,
    }
    return cbPost('v2/odds/lines', payload)

def getBetHistory():
    return cbGet('v4/bets/history')