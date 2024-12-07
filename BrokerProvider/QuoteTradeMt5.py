import os
from datetime import datetime
from KitaApi import QuoteProvider, TradeProvider, QuoteBar, KitaApi, Symbol

# import MetaTrader5 as mt5


class BrokerMt5(QuoteProvider, TradeProvider):
    provider_name = "Mt5"
    assets_file_name: str = "Assets_Pepperstone_Demo.csv"

    def __init__(self, parameter: str, data_rate: int):
        assets_path = os.path.join("Files", self.assets_file_name)
        QuoteProvider.__init__(self, parameter, assets_path, data_rate)
        TradeProvider.__init__(self, parameter)

    def __del__(self):
        pass

    def init_symbol(self, kita_api: KitaApi, symbol: Symbol, cache_path: str = ""):
        self.kita_api = kita_api
        self.symbol = symbol
        self.cache_path = cache_path
        pass

    def get_quote_bar_at_date(self, dt: datetime) -> tuple[str, QuoteBar]:
        return None  # type: ignore

    def get_first_quote_bar(self) -> tuple[str, QuoteBar]:
        return None  # type: ignore

    def get_next_quote_bar(self) -> tuple[str, QuoteBar]:
        return None  # type: ignore

    def read_quote_bar(self) -> tuple[str, QuoteBar]:
        return None  # type: ignore

    def update_account(self):
        return

    def add_profit(self, profit: float):
        return


# end of file