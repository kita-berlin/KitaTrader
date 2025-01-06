import os
from datetime import datetime
from Api.KitaApi import QuotesType, KitaApi, Symbol
from Api.QuoteProvider import QuoteProvider


class QuoteCsv(QuoteProvider):
    provider_name = "QuoteCsv"
    assets_file_name: str = "Assets_QuoteCsv.csv"

    def __init__(self, datarate: int, parameter: str = ""):
        assets_path = os.path.join("Files", self.assets_file_name)
        QuoteProvider.__init__(self, parameter, assets_path, datarate)
        self.file_handle = None

    def __del__(self):
        if self.file_handle is not None:
            self.file_handle.close()

    def init_symbol(self, api: KitaApi, symbol: Symbol):
        self.api = api
        self.symbol = symbol
        self.symbol_path = os.path.join(self.parameter, self.symbol.name)
        pass

    def get_day_at_utc(self, utc: datetime) -> tuple[str, datetime, QuotesType]:
        return None  # type: ignore
        pass

    def get_first_day(self) -> tuple[str, datetime, QuotesType]:
        return None  # type: ignore
        pass

    def read_quote(self) -> tuple[str, QuotesType]:
        return None  # type: ignore
        pass
