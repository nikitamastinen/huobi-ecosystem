import asyncio
from typing import Optional

from aiogram import Bot, Dispatcher, types
import datetime

from state import state, Context

from bot_control import async_trading_bot


def _get_help_response(value: str) -> Optional[str]:
    if value == 'help':
        return 'Пока не написал это'
    return None


def _get_state_response(value: str) -> Optional[str]:
    if value.lower() not in ['get', 'state', 'st', 'g']:
        return None
    return state.json()


def _get_context_response(value: str) -> Optional[str]:
    if value.lower() not in ['context', 'ct', 'ctx', 'ctxt']:
        return None
    return state.CONTEXT.value


async def _set_context(value: str, send, uid) -> Optional[str]:
    value = value.lower()
    if value in ['bal', 'ba', 'balance']:
        return str(state.MARKET[:-4]) + ': ' + str(await async_trading_bot.get_target_balance())

    elif value in ['s', 'b', 'buy', 'start']:
        asyncio.ensure_future(send("TRY BUY...", uid))
        await async_trading_bot.try_place_buy_limit()
        return "BUY order placed success"

    elif value in ['sell', 'se']:
        asyncio.ensure_future(send("TRY SELL...", uid))
        await async_trading_bot.try_place_sell_market()
        return "SELL order placed success"

    elif value in ['c', 'cancel']:
        asyncio.ensure_future(send("Begin CANCELLING orders...", uid))
        await async_trading_bot.cancel_all_orders()
        return "All orders cancelled"

    elif value in ['w', 'wait', 'terminate', 'q', 'stop', 'exit']:

        # тупой костыль
        for i in state.TRADING_TASKS_:
            i.close()
        state.TRADING_TASKS_.clear()

        return "Terminated"

    elif value in ['fetch_balance', 'fetch', 'f']:
        asyncio.ensure_future(send("Fetching balance...", uid))
        await async_trading_bot.fetch_balance()
        return "BALANCE=" + str(state.BASE_CURRENCY)

    return None


def _set_state(value: str) -> Optional[str]:
    if value == 'shutdown all bots':
        exit(0)
    value = value.replace(' ', '')
    print(value)
    msg = value.split('=')
    if not (len(msg) > 1 and len(msg[0]) > 0 and len(msg[1]) > 0):
        return None

    if msg[0].lower() == 'market':
        state.MARKET = msg[1]
        return 'MARKET = \'' + state.MARKET + '\''

    elif msg[0].lower() == 'balance' or msg[0].lower() == 'base_currency' or msg[0].lower() == 'base':
        try:
            float(msg[1])
        except ValueError:
            return None
        state.BASE_CURRENCY = float(msg[1])
        return 'BASE_CURRENCY = ' + str(state.BASE_CURRENCY)

    elif msg[0].lower() in ['price', 'pr', 'p']:
        try:
            float(msg[1])
        except ValueError:
            return None
        state.PRICE = float(msg[1])
        return 'PRICE = ' + str(state.PRICE)

    return None


def _test(value: str):
    if value.lower() == 'test':
        state.MARKET = 'gmtusdt'
        state.PRICE = 1.01
        state.BASE_CURRENCY = 10
        return state.json()
    return None


async def _response(value: str, send, uid) -> str:
    results = [
        _get_help_response(value),
        _get_state_response(value),
        _get_context_response(value),
        _set_state(value),
        await _set_context(value, send, uid),
        _test(value)
    ]
    for result in results:
        if result is not None:
            return result
    return 'Непонятный запрос'


class AsyncTelegramBot:
    def __init__(self, loop=asyncio.get_event_loop()):
        self.bot = Bot(token=state.TELEGRAM_BOT_KEY_)
        self.dp = Dispatcher(self.bot, loop=loop)

    async def send(self, message, uid):
        await self.bot.send_message(
            uid,
            message,
            parse_mode='HTML',
            disable_web_page_preview=True
        )

    async def run(self):
        await async_trading_bot.init()

        tasks = []

        @self.dp.message_handler(content_types=('text',))
        async def bot_control_(message: types.Message):
            if abs(message.date.timestamp() - 3 * 3600 - datetime.datetime.utcnow().timestamp()) > 30:
                print("Ignore old messages")
                return

            if int(message.from_user.id) not in state.ALLOWED_IDS_:
                return

            print(message.date)
            res = await _response(message.text, self.send, message.chat.id)
            await message.answer(
                res,
                parse_mode='HTML'
            )

        await self.dp.start_polling()
