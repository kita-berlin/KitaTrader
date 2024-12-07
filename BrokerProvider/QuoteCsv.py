import os
from datetime import datetime
from KitaApi import QuoteProvider, Bar, KitaApi, Symbol


class QuoteCsv(QuoteProvider):
    provider_name = "QuoteCsv"
    assets_file_name: str = "Assets_QuoteCsv.csv"

    def __init__(self, parameter: str, datarate: int):
        assets_path = os.path.join("Files", self.assets_file_name)
        QuoteProvider.__init__(self, parameter, assets_path, datarate)
        self.file_handle = None

    def __del__(self):
        if self.file_handle is not None:
            self.file_handle.close()

    def init_symbol(self, kita_api: KitaApi, symbol: Symbol, cache_path: str):
        self.kita_api = kita_api
        self.symbol = symbol
        self.cache_path = cache_path
        self.symbol_path = os.path.join(self.parameter, self.symbol.name)
        pass

    def get_quote_bar_at_datetime(self, dt: datetime) -> tuple[str, Bar]:
        return None  # type: ignore
        pass

    def get_first_quote_bar(self) -> tuple[str, Bar]:
        return None  # type: ignore
        pass

    def get_next_quote_bar(self) -> tuple[str, Bar]:
        return None  # type: ignore
        pass

    def read_quote_bar(self) -> tuple[str, Bar]:
        return None  # type: ignore
        pass
