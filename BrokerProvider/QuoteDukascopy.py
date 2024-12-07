import os
import struct
import requests
from datetime import datetime, timedelta
from lzma import LZMADecompressor, FORMAT_AUTO  # type: ignore
from Constants import Constants
from KitaApi import Quote, QuoteProvider, KitaApi, Symbol


class Dukascopy(QuoteProvider):
    provider_name = "Dukascopy"
    assets_file_name: str = "Assets_Dukascopy_Live.csv"

    WebRoot = "http://www.dukascopy.com/datafeed"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like\
		Gecko) Chrome/102.0.5005.61 Safari/537.36"
    }
    last_timestamp: float = 0
    is_last_tick_of_hour: bool = False

    def __init__(self, parameter: str, datarate: int):
        assets_path = os.path.join("Files", self.assets_file_name)
        QuoteProvider.__init__(self, parameter, assets_path, datarate)
        self.requests = requests.Session()
        self.requests.headers.update(self.headers)
        self.current_index = 0

    def init_symbol(self, kita_api: KitaApi, symbol: Symbol, cache_path: str):
        self.kita_api = kita_api
        self.symbol = symbol
        self.cache_path = os.path.join(cache_path, self.provider_name)
        if not os.path.exists(self.cache_path):
            os.makedirs(self.cache_path)

    def get_quote_bar_at_datetime(self, dt: datetime) -> tuple[str, Quote]:
        while True:
            timestamp = dt.replace(minute=0, second=0, microsecond=0).timestamp()
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
        return self.get_one_quote(timestamp)

    def get_one_quote(self, timestamp: float) -> tuple[str, Quote]:
        quote = Quote()
        error = ""

        try:
            timedelta = struct.unpack_from(">I", self.data, self.current_index)[0]
            quote.ask = round(
                struct.unpack_from(">I", self.data, self.current_index + 4)[0]
                * self.symbol.point_size,
                self.symbol.digits,
            )
            quote.bid = round(
                struct.unpack_from(">I", self.data, self.current_index + 8)[0]
                * self.symbol.point_size,
                self.symbol.digits,
            )

            # Python timestamp is microseconds since 1.1.1970
            # Ducascopy timedelta is milliseconds since hour start
            quote.timestamp = timestamp + timedelta / 1e3
            self.current_index += 20

            self.is_last_tick_of_hour = self.current_index >= len(self.data)

        except Exception as e:
            error = str(e)

        self.last_timestamp = timestamp
        return error, quote

    def get_next_quote_bar(self) -> tuple[str, Quote]:
        if self.is_last_tick_of_hour:
            self.last_timestamp += Constants.SEC_PER_HOUR
            return self.get_quote_bar_at_datetime(
                datetime.fromtimestamp(self.last_timestamp)
            )
        else:
            return self.get_one_quote(self.last_timestamp)

    def get_first_quote_bar(self) -> tuple[str, Quote]:
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

        return self.get_quote_bar_at_datetime(end_date)

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
