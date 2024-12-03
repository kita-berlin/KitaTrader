# from datetime import datetime
from KitaApi import TradeProvider, Account


class BrokerPaper(TradeProvider):
    def __init__(self, parameter: str, account: Account):
        TradeProvider.__init__(self, parameter, account)

    def initialize(self, symbol_name: str, account: Account):
        self.symbol_name = symbol_name
        self.account = account
        pass

    def update_account(self):
        pass
