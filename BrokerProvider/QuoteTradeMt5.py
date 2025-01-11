import os
import MetaTrader5 as mt5 # type: ignore
from datetime import datetime
from Api.KitaApi import TradeProvider, KitaApi, Symbol
from Api.Bars import Bars
from Api.QuoteProvider import QuoteProvider


class BrokerMt5(QuoteProvider, TradeProvider):
    provider_name = "Mt5"
    assets_file_name: str = "Assets_Pepperstone_Demo.csv"

    def __init__(self, parameter: str, data_rate: int):
        assets_path = os.path.join("Files", self.assets_file_name)
        QuoteProvider.__init__(self, parameter, assets_path, data_rate)
        TradeProvider.__init__(self, parameter)

    def __del__(self):
        pass

    def init_symbol(self, api: KitaApi, symbol: Symbol, cache_path: str = ""):
        self.api = api
        self.symbol = symbol
        self.cache_path = cache_path
        pass

    def get_day_at_utc(self, utc: datetime) -> tuple[str, datetime, Bars]:
        return None  # type: ignore

    def get_first_datetime(self) -> tuple[str, datetime]:
        return None  # type: ignore

    def read_quote(self) -> tuple[str, Bars]:
        return None  # type: ignore

    def update_account(self):
        return

    def add_profit(self, profit: float):
        return


# end of file