import os
from datetime import datetime
from Api.KitaApi import KitaApi, Symbol
from Api.Bars import Bars
from Api.QuoteProvider import QuoteProvider


class QuoteCsv(QuoteProvider):
    provider_name = "QuoteCsv"
    assets_file_name: str = "Assets_QuoteCsv.csv"

    def __init__(self, data_rate: int, parameter: str = ""):
        assets_path = os.path.join("Files", self.assets_file_name)
        QuoteProvider.__init__(self, parameter, assets_path, data_rate)
        self.file_handle = None

    def __del__(self):
        if self.file_handle is not None:
            self.file_handle.close()

    def init_symbol(self, api: KitaApi, symbol: Symbol):
        self.api = api
        self.symbol = symbol
        self.symbol_path = os.path.join(self.parameter, self.symbol.name)
        pass

    def get_day_at_utc(self, utc: datetime) -> tuple[str, datetime, Bars]:
        return None  # type: ignore
        pass

    def get_first_datetime(self) -> tuple[str, datetime]:
        return None  # type: ignore
        pass

    def read_quote(self) -> tuple[str, Bars]:
        return None  # type: ignore
        pass
