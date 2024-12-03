# from datetime import datetime
from KitaApi import TradeProvider, KitaApi


class BrokerPaper(TradeProvider):
    def __init__(self, parameter: str):
        TradeProvider.__init__(self, parameter)

    def initialize(self, symbol_name: str, kita_api: KitaApi):
        self.symbol_name = symbol_name
        self.kita_api = kita_api
        pass

    def update_account(self):
        pass

    def add_profit(self, profit: float):
        self.kita_api.account.balance += profit
