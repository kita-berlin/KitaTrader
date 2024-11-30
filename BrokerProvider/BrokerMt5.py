#import MetaTrader5 as mt5
from datetime import datetime
from AlgoApi import Account, BrokerProvider, QuoteBar


class BrokerMt5(BrokerProvider):
    def __init__(self, parameter: str, data_rate: int, account: Account):
        super().__init__(parameter, data_rate, account)

    def __del__(self):
        pass

    def initialize(self, symbol_name: str):
        self.symbol_name = symbol_name
        pass

    def get_quote_bar_at_date(self, dt: datetime) -> tuple[str, QuoteBar]:
        return None  # type: ignore
        pass

    def get_first_quote_bar(self) -> tuple[str, QuoteBar]:
        return None  # type: ignore
        pass

    def get_next_quote_bar(self) -> tuple[str, QuoteBar]:
        return None  # type: ignore
        pass

    def read_quote_bar(self) -> tuple[str, QuoteBar]:
        return None  # type: ignore
        pass

    def update_account(self):
        pass
