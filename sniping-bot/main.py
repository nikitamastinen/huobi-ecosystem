import asyncio

from bot_control import AsyncTradingBot
from telegram_control import AsyncTelegramBot


def run():
    # limit_market_bot = AsyncTradingBot()
    telegram_bot = AsyncTelegramBot()

    loop = asyncio.new_event_loop()
    # loop.create_task(limit_market_bot.run())
    loop.create_task(telegram_bot.run())
    loop.run_forever()


run()
