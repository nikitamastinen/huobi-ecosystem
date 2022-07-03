import datetime
import hmac
import json
import time
from operator import itemgetter

import requests
import hashlib
import base64

from urllib.parse import urlencode
import asyncio
import aiohttp
from aiohttp import ClientSession


def get_deposits():
    with open("accounts.json", "r") as read_file:  # файл со всеми параметрами
        data = json.load(read_file)

    for account in data.values():
        print(account['usdt_deposit'])


async def get_balance(API_KEY: str, API_SECRET: str, ACCOUNT_ID: str):
    AccessKeyId = API_KEY
    SecretKey = API_SECRET
    timestamp = datetime.datetime.fromtimestamp(time.time() - 3 * 60 * 60).strftime("%Y-%m-%dT%H:%M:%S")
    params = urlencode({'AccessKeyId': AccessKeyId,
                        'SignatureMethod': 'HmacSHA256',
                        'SignatureVersion': '2',
                        'Timestamp': timestamp
                        })

    account_id = ACCOUNT_ID
    base_uri = 'api.huobi.pro'

    method = 'GET'
    endpoint = '/v1/account/accounts/{}/balance'.format(account_id)
    pre_signed_text = method + '\n' + base_uri + '\n' + endpoint + '\n' + params
    hash_code = hmac.new(API_SECRET.encode(), pre_signed_text.encode(), hashlib.sha256).digest()
    signature = urlencode({'Signature': base64.b64encode(hash_code).decode()})
    url = 'https://' + base_uri + endpoint + '?' + params + '&' + signature
    response = requests.request(method, url)

    answer = []

    data = response.json()['data']['list']

    for token in data:
        if token['balance'] != '0':
            answer.append([token['currency'], token['balance']])

    sorted(answer, key=itemgetter(1))
    return answer
res = 0
v = []

async def get_usdt_balance(API_KEY: str, API_SECRET: str, ACCOUNT_ID: str, NAME: str):
    try:
        AccessKeyId = API_KEY
        SecretKey = API_SECRET
        timestamp = datetime.datetime.fromtimestamp(time.time() - 3 * 60 * 60).strftime("%Y-%m-%dT%H:%M:%S")
        params = urlencode({'AccessKeyId': AccessKeyId,
                            'SignatureMethod': 'HmacSHA256',
                            'SignatureVersion': '2',
                            'Timestamp': timestamp
                            })

        account_id = ACCOUNT_ID
        base_uri = 'api.huobi.pro'

        method = 'GET'
        endpoint = '/v1/account/accounts/{}/balance'.format(account_id)
        pre_signed_text = method + '\n' + base_uri + '\n' + endpoint + '\n' + params
        hash_code = hmac.new(API_SECRET.encode(), pre_signed_text.encode(), hashlib.sha256).digest()
        signature = urlencode({'Signature': base64.b64encode(hash_code).decode()})
        url = 'https://' + base_uri + endpoint + '?' + params + '&' + signature
        async with ClientSession() as client_session:
            response = await client_session.request(method, url)
            response = await response.text()
            response = json.loads(response)
            answer = []

            data = response['data']['list']
            for token in data:
                if token['currency'] == 'usdt' and token['type'] == 'trade':
                    v.append((NAME, token['balance']))

                    global res
                    res += float(token['balance'])

                    return token['balance']
    except:
        print(response)
        return None
    return None

answer = 0
if __name__ == "__main__":
    with open("data.json", "r") as read_file:  # файл со всеми параметрами
        data = json.load(read_file)
    tsk = []
    for account in data:

        tsk.append(get_usdt_balance(API_KEY=account['API_KEY'], API_SECRET=account["API_SECRET"],
                               ACCOUNT_ID=account['SPOT_ID'], NAME=account['MAIL']))
        # print(account['MAIL'], sum)
        # answer += float(sum)

    async def run():
        await asyncio.gather(*tsk)
    asyncio.run(run())
        # print(get_balance(API_KEY=account['api_key'], API_SECRET=account["api_secret"],ACCOUNT_ID=account['spot_id']))
    v.sort()
    for i in v:
        print(i[0], i[1])
    print("итого ")
    print(res)
    # get_deposits()

