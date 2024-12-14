import os
import struct
import requests
from datetime import datetime, timedelta
from lzma import LZMADecompressor, FORMAT_AUTO  # type: ignore
from KitaApi import QuoteProvider, KitaApi, Symbol, QuoteType, QuotesType

# Instead of numpy arrays we are using QuotesType] as a temporary container 
# and later convert it to a NumPy array to avoid frequent memory reallocations.

class Dukascopy(QuoteProvider):
    provider_name = "Dukascopy"
    assets_file_name: str = "Assets_Dukascopy_Live.csv"

    WebRoot = "http://www.dukascopy.com/datafeed"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like\
		Gecko) Chrome/102.0.5005.61 Safari/537.36"
    }
    last_hour_base_timestamp: float = 0

    def __init__(self, parameter: str, datarate: int):
        assets_path = os.path.join("Files", self.assets_file_name)
        QuoteProvider.__init__(self, parameter, assets_path, datarate)
        self.requests = requests.Session()
        self.requests.headers.update(self.headers)

    def init_symbol(self, api: KitaApi, symbol: Symbol):
        self.api = api
        self.symbol = symbol
        self.cache_path = os.path.join(api.cache_path, self.provider_name)
        if not os.path.exists(self.cache_path):
            os.makedirs(self.cache_path)

    def get_day_at_utc(self, utc: datetime) -> tuple[str, datetime, QuotesType]:
        day_data: QuotesType = []
        self.last_utc = run_utc = utc.replace(hour=0, minute=0, second=0, microsecond=0)

        while True:
            url = self._get_url(self.WebRoot, run_utc, self.symbol.name)
            path = self._get_file_name(self.cache_path, run_utc, self.symbol.name)
            if os.path.exists(path):
                with open(path, "rb") as file:
                    data = file.read()
            else:
                try:
                    response = self.requests.get(url, stream=True)
                    response.raise_for_status()
                    decompressor = LZMADecompressor()
                    raw_data = response.content
                    data = decompressor.decompress(raw_data)
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    with open(path, "wb") as new_file:
                        new_file.write(data)
                except Exception as e:
                    return str(e), self.last_utc, None  # type: ignore

            if len(data) > 0:
                day_data += self._get_hour(run_utc, data)

            run_utc += timedelta(hours=1)
            if run_utc.date() > utc.date():
                break

        return "", self.last_utc, day_data

    def find_first_day(self) -> tuple[str, datetime, QuotesType]:
        start_date = datetime(2000, 1, 1)
        end_date = datetime.now()

        while (end_date - start_date).days > 1:
            mid_date = start_date + (end_date - start_date) / 2
            url = self._get_url(Dukascopy.WebRoot, mid_date, self.symbol.name)
            try:
                response = self.requests.get(url, stream=True)
                response.raise_for_status()
                end_date = mid_date
            except requests.RequestException:
                start_date = mid_date

        return self.get_day_at_utc(end_date)

    def _get_hour(self, hour_base_time: datetime, data: bytes) -> QuotesType:
        hour: QuotesType = []
        current_index: int = 0
        hour_base_timestamp = hour_base_time.timestamp()

        while True:
            quote: QuoteType = []
            # Python timestamp is microseconds since 1.1.1970
            # Ducascopy timedelta is milliseconds since hour start
            timestamp: float = (
                hour_base_timestamp
                + struct.unpack_from(">I", data, current_index)[0] / 1e3
            )

            ask = round(
                struct.unpack_from(">I", data, current_index + 4)[0]
                * self.symbol.point_size,
                self.symbol.digits,
            )
            bid = round(
                struct.unpack_from(">I", data, current_index + 8)[0]
                * self.symbol.point_size,
                self.symbol.digits,
            )

            quote.append(timestamp)
            quote.append(bid)
            quote.append(ask)
            hour.append(quote)
            current_index += 20
            if current_index >= len(data):
                break

        return hour

    def _get_url(self, base_url: str, utc: datetime, symbol_name: str) -> str:
        return f"{base_url}/{symbol_name}/{utc.year}/{utc.month - 1:02}/{utc.day:02}/{utc.hour:02}h_ticks.bi5"

    def _get_file_name(self, cache_path: str, utc: datetime, symbol_name: str) -> str:
        return os.path.join(
            cache_path,
            symbol_name,
            "bi5",
            f"{utc.year:04}",
            f"{utc.month - 1:02}",
            f"{utc.day:02}",
            f"{utc.hour:02}h_ticks.bi5",
        )


# end of file
