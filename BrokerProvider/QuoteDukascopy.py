import os
import struct
import requests
import pytz
from datetime import datetime, timedelta
from datetime import datetime, timedelta
from lzma import LZMADecompressor, FORMAT_AUTO  # type: ignore
from KitaApi import QuoteBar, QuoteProvider, KitaApi, Symbol


class Dukascopy(QuoteProvider):
    provider_name = "Dukascopy"
    assets_file_name: str = "Assets_Dukascopy_Live.csv"

    WebRoot = "http://www.dukascopy.com/datafeed"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like\
		Gecko) Chrome/102.0.5005.61 Safari/537.36"
    }
    last_dt: datetime = datetime.min
    is_last_tick_of_hour: bool = False

    def __init__(self, parameter: str, data_rate: int):
        QuoteProvider.__init__(self, parameter, data_rate)
        self.requests = requests.Session()
        self.requests.headers.update(self.headers)
        self.current_index = 0

    def initialize(self, kita_api: KitaApi, symbol: Symbol, cache_path: str):
        self.kita_api = kita_api
        self.symbol = symbol
        self.cache_path = os.path.join(cache_path, self.provider_name)
        if not os.path.exists(self.cache_path):
            os.makedirs(self.cache_path)

    def get_quote_bar_at_date(self, dt: datetime) -> tuple[str, QuoteBar]:
        while True:
            dt = dt.replace(minute=0, second=0, microsecond=0)
            url = self.get_url(self.WebRoot, dt, self.symbol.name)
            path = self.get_file_name(self.cache_path, dt, self.symbol.name)
            if os.path.exists(path):
                with open(path, "rb") as file:
                    self.data = file.read()
            else:
                try:
                    response = self.requests.get(url, stream=True)
                    response.raise_for_status()
                    decompressor = LZMADecompressor()
                    raw_data = response.content
                    self.data = decompressor.decompress(raw_data)
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    with open(path, "wb") as new_file:
                        new_file.write(self.data)
                except Exception as e:
                    return str(e), None  # type: ignore

            if 0 == len(self.data):
                dt += timedelta(hours=1)
            else:
                break

        self.current_index = 0
        return self.get_one_quote(dt)

    def get_one_quote(self, dt: datetime) -> tuple[str, QuoteBar]:
        quote = QuoteBar()
        error = ""

        try:
            time_delta = struct.unpack_from(">I", self.data, self.current_index)[0]
            ask = (
                struct.unpack_from(">I", self.data, self.current_index + 4)[0]
                * self.symbol.point_size
            )
            quote.open = quote.high = quote.low = quote.close = round(
                struct.unpack_from(">I", self.data, self.current_index + 8)[0]
                * self.symbol.point_size,
                self.symbol.digits,
            )
            quote.volume = struct.unpack_from(">f", self.data, self.current_index + 12)[
                0
            ]
            quote.volume += struct.unpack_from(
                ">f", self.data, self.current_index + 16
            )[0]
            quote.time = (dt + timedelta(milliseconds=time_delta)).astimezone(pytz.utc)
            quote.open_spread = round(ask - quote.open, self.symbol.digits)
            self.current_index += 20

            self.is_last_tick_of_hour = self.current_index >= len(self.data)

        except Exception as e:
            error = str(e)

        self.last_dt = dt
        return error, quote

    def get_next_quote_bar(self) -> tuple[str, QuoteBar]:
        if self.is_last_tick_of_hour:
            self.last_dt += timedelta(hours=1)
            return self.get_quote_bar_at_date(self.last_dt)
        else:
            return self.get_one_quote(self.last_dt)

    def get_first_quote_bar(self) -> tuple[str, QuoteBar]:
        start_date = datetime(2000, 1, 1)
        end_date = datetime.now()

        while (end_date - start_date).days > 1:
            mid_date = start_date + (end_date - start_date) / 2
            url = self.get_url(Dukascopy.WebRoot, mid_date, self.symbol.name)
            try:
                response = self.requests.get(url, stream=True)
                response.raise_for_status()
                end_date = mid_date
            except requests.RequestException:
                start_date = mid_date

        return self.get_quote_bar_at_date(end_date)

    def get_url(self, base_url: str, dt: datetime, symbol_name: str) -> str:
        return f"{base_url}/{symbol_name}/{dt.year}/{dt.month - 1:02}/{dt.day:02}/{dt.hour:02}h_ticks.bi5"

    def get_file_name(self, cache_path: str, dt: datetime, symbol_name: str) -> str:
        return os.path.join(
            cache_path,
            symbol_name,
            "bi5",
            f"{dt.year:04}",
            f"{dt.month - 1:02}",
            f"{dt.day:02}",
            f"{dt.hour:02}h_ticks.bi5",
        )


# end of file
