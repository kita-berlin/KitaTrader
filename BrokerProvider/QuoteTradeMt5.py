import os
from datetime import datetime
from KitaApi import QuoteProvider, TradeProvider, Quote, KitaApi, Symbol

# import MetaTrader5 as mt5


class BrokerMt5(QuoteProvider, TradeProvider):
    provider_name = "Mt5"
    assets_file_name: str = "Assets_Pepperstone_Demo.csv"

    def __init__(self, parameter: str, datarate: int):
        assets_path = os.path.join("Files", self.assets_file_name)
        QuoteProvider.__init__(self, parameter, assets_path, datarate)
        TradeProvider.__init__(self, parameter)

    def __del__(self):
        pass

    def init_symbol(self, api: KitaApi, symbol: Symbol, cache_path: str = ""):
        self.api = api
        self.symbol = symbol
        self.cache_path = cache_path
        pass

    def get_day_at_utc(self, dt: datetime) -> tuple[str, Quote]:
        return None  # type: ignore

    def find_first_day(self) -> tuple[str, Quote]:
        return None  # type: ignore

    def get_next_day(self) -> tuple[str, Quote]:
        return None  # type: ignore

    def read_quote(self) -> tuple[str, Quote]:
        return None  # type: ignore

    def update_account(self):
        return

    def add_profit(self, profit: float):
        return


# end of file