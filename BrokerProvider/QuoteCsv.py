import os
from datetime import datetime
from KitaApi import QuoteProvider, Quote, KitaApi, Symbol


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

    def init_symbol(self, api: KitaApi, symbol: Symbol):
        self.api = api
        self.symbol = symbol
        self.symbol_path = os.path.join(self.parameter, self.symbol.name)
        pass

    def get_day_at_utc(self, dt: datetime) -> tuple[str, Quote]:
        return None  # type: ignore
        pass

    def find_first_day(self) -> tuple[str, Quote]:
        return None  # type: ignore
        pass

    def get_next_day(self) -> tuple[str, Quote]:
        return None  # type: ignore
        pass

    def read_quote(self) -> tuple[str, Quote]:
        return None  # type: ignore
        pass
