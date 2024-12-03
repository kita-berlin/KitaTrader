# import MetaTrader5 as mt5
from datetime import datetime
from KitaApi import Account, QuoteProvider, TradeProvider, QuoteBar


class BrokerMt5(QuoteProvider, TradeProvider):
    def __init__(self, parameter: str, data_rate: int, account: Account):
        QuoteProvider.__init__(self, parameter, data_rate)
        TradeProvider.__init__(self, parameter, account)

    def __del__(self):
        pass

    def initialize(self, parameter: str, account: Account):
        #self.symbol_name = symbol_name
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
