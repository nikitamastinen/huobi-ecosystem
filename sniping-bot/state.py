import json
from enum import Enum
from sys import argv

from _constants import (
    TELEGRAM_BOT_KEY_,
    ALLOWED_IDS_
)


class Context(str, Enum):
    INIT = 'Initializing...'
    WAIT = 'Waiting...'
    TRY_PLACE_BUY_LIMIT = 'TRYING TO BUY...'
    TRY_PLACE_SELL_MARKET = 'TRYING TO SELL...'
    CANCEL_OPENED_ORDERS = 'CANCELING ORDERS...'
    BUY_LIMIT_SET = 'BUY LIMIT ORDER SET'
    SELL_MARKET_SET = 'SELL MARKET ORDER SET'
    TERMINATE = 'Terminating process...'
    FETCHING_BALANCE = 'Fetching balance...'


class State:
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.INSTANCE_ = super(State, cls).__new__(cls)
        return cls.INSTANCE_    # Это работает, хоть он и подсвечивает

    def __init__(self):
        self.CONTEXT = Context.WAIT

        self.TELEGRAM_BOT_KEY_ = TELEGRAM_BOT_KEY_
        self.ALLOWED_IDS_ = ALLOWED_IDS_
        self.TRADING_TASKS_ = []

        try:
            self.ID = argv[1]
            self.API_KEY_ = argv[2]
            self.API_SECRET_ = argv[3]
            self.ACCOUNT_ID_ = None
            self.SPOT_ID_ = int(argv[5])
            self.INTERVAL_ = 0.025
            self.TELEGRAM_BOT_KEY_ = argv[7]
            self.BASE_CURRENCY = 0.0
        except IndexError:
            self.API_KEY_ = "7eaa652a-77b16ac1-b1c1a5bb-mk0lklo0de"
            self.API_SECRET_ = "a14219f2-9e71583f-a4b7015f-1b34b"
            self.SPOT_ID_ = 48765284
            self.INTERVAL_ = 0.025
            self.BASE_CURRENCY = 1

        self.MARKET = 'gmtusdt'

        self.PRICE = 1.01

    def json(self):
        fields = dict()

        for (key, val) in self.__dict__.items():
            if len(key) >= 2 and key[-1] != '_':
                fields[key] = val

        return json.dumps(fields, indent=2)


state = State()

# other_state = State()
#
# print(state is other_state)
#
# state.PRICE = 1000
#
# print(other_state.PRICE)
