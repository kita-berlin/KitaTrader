# from datetime import datetime
from KitaApi import TradeProvider, KitaApi, Symbol


class TradePaper(TradeProvider):
    def __init__(self, parameter: str):
        TradeProvider.__init__(self, parameter)

    def init_symbol(self, api: KitaApi, symbol: Symbol, cache_path: str = ""):
        self.symbol = symbol
        self.api = api
        pass

    def update_account(self):
        pass

    # change to: close trade etc. All trading functions must end up here because they might be have to be sent to the broker
    def add_profit(self, profit: float):
        self.api.account.balance += profit
