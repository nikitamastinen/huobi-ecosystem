import asyncio
import base64
import datetime
import decimal
import hashlib
import hmac
import json
from decimal import Decimal
from typing import List, Tuple, Coroutine, Optional
from urllib.parse import urlencode

import aiohttp
from aiohttp import ClientSession

from state import state, Context


async def _async_task_schedule(functions: List[Tuple[float, Coroutine]]):
    async def f_call(time_shift, f):
        await asyncio.sleep(time_shift)
        await f

    tasks = [f_call(time_shift, f) for (time_shift, f) in functions]
    state.TRADING_TASKS_ += tasks

    f = asyncio.gather(*tasks)
    try:
        await f
    except asyncio.CancelledError:
        for i in tasks:
            i.close()
        raise


API_KEY = state.API_KEY_
API_SECRET = state.API_SECRET_
SPOT_ID = state.SPOT_ID_
INTERVAL = state.INTERVAL_


class HuobiBot:
    def __init__(self, rq_interval=INTERVAL):
        self.RQ_INTERVAL = rq_interval
        self.NUM_OF_BUY_ITERATIONS = 512

        self.client_session: Optional[ClientSession] = None
        self.loop = asyncio.get_event_loop()
        self.current_balance = 0.0

    async def init_session(self):
        self.client_session: ClientSession = ClientSession()

    async def place_order(self, market: str, amount: float, order_type='buy'):
        timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")

        params_dict = {
            'AccessKeyId': API_KEY,
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'Timestamp': timestamp
        }
        params_url_enc = urlencode(sorted(params_dict.items(), key=lambda tup: tup[0]))

        pre_signed = 'POST\n'
        pre_signed += 'api.huobi.pro\n'
        pre_signed += f'/v1/order/orders/place\n'
        pre_signed += params_url_enc

        if state.PRICE == 0:
            raise asyncio.CancelledError
        if order_type == 'buy':
            body = {
                'account-id': SPOT_ID,
                'symbol': market,
                'type': f'{order_type}-limit',

                'amount': float(
                    Decimal(state.BASE_CURRENCY / state.PRICE).quantize(Decimal('.01'), rounding=decimal.ROUND_DOWN)),
                'price': state.PRICE,
            }
            print("TRY BUY...")
        else:
            body = {
                'account-id': SPOT_ID,
                'symbol': market,
                'type': f'{order_type}-market',
                'amount': amount
            }
            print("TRY SELL...")

        sig_bin = hmac.new(
            API_SECRET.encode(),
            pre_signed.encode(),
            hashlib.sha256).digest()
        sig_b64_bytes = base64.b64encode(sig_bin)
        sig_b64_str = sig_b64_bytes.decode()
        sig_url = urlencode({'Signature': sig_b64_str})

        url = 'https://api.huobi.pro/v1/order/orders/place?'
        url += params_url_enc + '&'
        url += sig_url

        resp = await self.client_session.post(url, json=body)
        result = await resp.text()
        print(order_type.capitalize(), result)
        if json.loads(result)['status'] == 'ok':
            raise asyncio.CancelledError

    async def get_open_orders(self):
        print("enter")
        # currency = market[:-len('usdt')]
        # print(currency)
        AccessKeyId = API_KEY
        SecretKey = API_SECRET
        timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
        params = urlencode({'AccessKeyId': AccessKeyId,
                            'SignatureMethod': 'HmacSHA256',
                            'SignatureVersion': '2',
                            'Timestamp': timestamp
                            })

        account_id = SPOT_ID
        base_uri = 'api.huobi.pro'

        body = {
            'account-id': SPOT_ID,
        }

        method = 'GET'
        endpoint = '/v1/order/openOrders'.format(account_id)
        pre_signed_text = method + '\n' + base_uri + '\n' + endpoint + '\n' + params
        hash_code = hmac.new(API_SECRET.encode(), pre_signed_text.encode(), hashlib.sha256).digest()
        signature = urlencode({'Signature': base64.b64encode(hash_code).decode()})
        url = 'https://' + base_uri + endpoint + '?' + params + '&' + signature

        response = await self.client_session.request(method, url)
        data = json.loads(await response.text())
        print(data)
        return data

    async def close_all_open_orders(self):
        print("enter")
        # currency = market[:-len('usdt')]
        # print(currency)
        AccessKeyId = API_KEY
        SecretKey = API_SECRET
        timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
        params = urlencode({'AccessKeyId': AccessKeyId,
                            'SignatureMethod': 'HmacSHA256',
                            'SignatureVersion': '2',
                            'Timestamp': timestamp
                            })

        account_id = SPOT_ID
        base_uri = 'api.huobi.pro'

        id = await self.get_open_orders()
        if len(id['data']) == 0:
            return
        body = {
            'account-id': SPOT_ID,
            "client-order-id": str(id['data'][0]['id'])
        }

        method = 'POST'
        endpoint = '/v1/order/orders/{}/submitcancel'.format(id['data'][0]['id'])
        pre_signed_text = method + '\n' + base_uri + '\n' + endpoint + '\n' + params
        hash_code = hmac.new(API_SECRET.encode(), pre_signed_text.encode(), hashlib.sha256).digest()
        signature = urlencode({'Signature': base64.b64encode(hash_code).decode()})
        url = 'https://' + base_uri + endpoint + '?' + params + '&' + signature

        response = await self.client_session.post(url, json=body)
        data = json.loads(await response.text())
        print(data)

    async def get_balance(self, market: str):
        currency = market[:-len('usdt')]
        print(currency)
        AccessKeyId = API_KEY
        SecretKey = API_SECRET
        timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
        params = urlencode({'AccessKeyId': AccessKeyId,
                            'SignatureMethod': 'HmacSHA256',
                            'SignatureVersion': '2',
                            'Timestamp': timestamp
                            })

        account_id = SPOT_ID
        base_uri = 'api.huobi.pro'

        method = 'GET'
        endpoint = '/v1/account/accounts/{}/balance'.format(account_id)
        pre_signed_text = method + '\n' + base_uri + '\n' + endpoint + '\n' + params
        hash_code = hmac.new(API_SECRET.encode(), pre_signed_text.encode(), hashlib.sha256).digest()
        signature = urlencode({'Signature': base64.b64encode(hash_code).decode()})
        url = 'https://' + base_uri + endpoint + '?' + params + '&' + signature
        response = await self.client_session.request(method, url)
        data = json.loads(await response.text())

        # print(data)

        for token in data['data']['list']:
            if token['currency'] == currency:
                print("BALANCE IS", token)
                self.current_balance = max(0.0, float(
                    Decimal(token['balance']).quantize(Decimal('.01'), rounding=decimal.ROUND_DOWN)))
                return self.current_balance

    async def place_order_mock(self):
        print("att")
        await asyncio.sleep(2)
        raise asyncio.CancelledError

    async def try_place_buy_limit(self):
        print("ENTER")
        function_list = []
        for i in range(self.NUM_OF_BUY_ITERATIONS):
            function_list.append((state.INTERVAL_ * i, self.place_order(state.MARKET, state.BASE_CURRENCY)))
        await _async_task_schedule(function_list)

    async def try_place_sell_market(self):
        self.current_balance = await self.get_balance(state.MARKET)

        print(
            '////////////////////////////////////////////////BALANCE RECEIVED////////////////////////////////////////')
        # time.sleep(TIME_BEFORE_SELL)

        function_list = [
            (
                0,
                self.place_order(
                    state.MARKET,
                    float(
                        Decimal(self.current_balance * 0.999).quantize(Decimal('.001'),
                                                                       rounding=decimal.ROUND_DOWN)
                    ),
                    'sell'
                )
            )
        ]

        await _async_task_schedule(function_list)

    async def get_all_orders(self):
        try:
            await self.close_all_open_orders()
        finally:
            pass

    def run(self):
        # self.loop.run_until_complete(self.close_all_open_orders())
        # return
        # return
        # MARKET = 'cudosusdt'
        function_list = []
        # for i in range(self.NUM_OF_BUY_ITERATIONS):
        # function_list.append((self.RQ_INTERVAL * i, self.place_order(MARKET, BASE_CURRENCY)))
        # function_list.append((self.RQ_INTERVAL * i, self.get_balance(MARKET)))

        try:
            self.loop.run_until_complete(_async_task_schedule(function_list))
        except Exception as err:
            try:
                self.loop.stop()
                self.loop.close()
            except Exception as err:
                pass
            print("//////////////////////////////////////////SELL////////////////////////////////////////////////")

        asyncio.set_event_loop(asyncio.new_event_loop())
        self.loop = asyncio.get_event_loop()
        self.client_session = aiohttp.ClientSession()

        self.run_get_balance(state.MARKET)
        balance = self.current_balance

        print(
            '////////////////////////////////////////////////BALANCE RECEIVED////////////////////////////////////////')
        print(balance)
        # time.sleep(TIME_BEFORE_SELL)

        function_list = []
        for i in range(15):
            function_list.append((i, self.place_order(state.MARKET, float(
                Decimal(self.current_balance * 0.999).quantize(Decimal('.01'),
                                                               rounding=decimal.ROUND_DOWN)),
                                                      'sell')))
        try:
            self.loop.run_until_complete(_async_task_schedule(function_list))
        except Exception as e:
            print("DONE", e)

        self.loop.run_until_complete(self.close_all_open_orders())


class AsyncTradingBot:
    def __init__(self):
        self.bot = HuobiBot()

    async def get_target_balance(self):
        return await self.bot.get_balance(state.MARKET)

    async def try_place_buy_limit(self):
        task = self.bot.try_place_buy_limit()
        state.TRADING_TASKS_.append(task)
        try:
            await task
        except BaseException:
            state.CONTEXT = state.CONTEXT.BUY_LIMIT_SET
            print("BUY LIMIT SET")

    async def cancel_all_orders(self):
        task = self.bot.close_all_open_orders()
        state.TRADING_TASKS_.append(task)
        try:
            await task
        except BaseException as err:
            print(err)

        print("ORDERS CANCELLED")
        state.CONTEXT = Context.WAIT

    async def try_place_sell_market(self):
        task = self.bot.try_place_sell_market()
        state.TRADING_TASKS_.append(task)
        try:
            await task
        except BaseException:
            print("SELL MARKET SET")
        # state.CONTEXT = Context.WAIT

    async def init(self):
        await self.bot.init_session()

    async def wait(self):
        raise asyncio.CancelledError

    async def fetch_balance(self):
        state.BASE_CURRENCY = int(await self.bot.get_balance('usdtusdt'))
        print("b", state.BASE_CURRENCY)

        state.CONTEXT = Context.WAIT

    async def run(self):
        await self.bot.init_session()
        while True:
            print("iteration............................................")

            tasks = [
                self.try_place_buy_limit(),
                self.cancel_all_orders(),
                self.try_place_sell_market(),
                self.fetch_balance(),
                self.wait()
            ]
            f = asyncio.gather(*tasks)

            try:
                await f
            except BaseException:
                print("Terminating...")

                for i in state.TRADING_TASKS_:
                    i.close()
                state.TRADING_TASKS_.clear()

                for i in tasks:
                    i.close()
                await asyncio.sleep(0)


async_trading_bot = AsyncTradingBot()
