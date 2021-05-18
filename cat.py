# Cat images for Beardless Bot

import requests
from sys import exit as sysExit

def cat(key):
    r = requests.get("https://api.thecatapi.com/v1/images/search", params={"limit": 1, "size": "full"}, headers={'x-api-key': key})
    if r.status_code == 200:
        return(r.json()[0]['url'])
    else:
        print(r.status_code)
        raise Exception("API Limit Reached!")