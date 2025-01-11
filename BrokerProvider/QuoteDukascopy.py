import os
import struct
import requests
from datetime import datetime, timedelta
from lzma import LZMADecompressor, FORMAT_AUTO  # type: ignore
from Api.KitaApi import KitaApi, Symbol
from Api.Bars import Bars
from Api.QuoteProvider import QuoteProvider


class Dukascopy(QuoteProvider):
    provider_name = "Dukascopy"
    _assets_file_name: str = "Assets_Dukascopy_Live.csv"

    _web_root = "http://www.dukascopy.com/datafeed"
    _headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like\
		Gecko) Chrome/102.0.5005.61 Safari/537.36"
    }
    _last_hour_base_timestamp: float = 0

    def __init__(self, data_rate: int, parameter: str = ""):
        assets_path = os.path.join("Files", self._assets_file_name)
        QuoteProvider.__init__(self, parameter, assets_path, data_rate)
        self.requests = requests.Session()
        self.requests.headers.update(self._headers)

    def init_symbol(self, api: KitaApi, symbol: Symbol):
        self.api = api
        self.symbol = symbol
        self.cache_path = os.path.join(api.DataPath, self.provider_name, "cache")

    def get_day_at_utc(self, utc: datetime) -> tuple[str, datetime, Bars]:
        day_data: Bars = Bars(self.symbol.name, 0, 0)
        self.last_utc = run_utc = utc.replace(hour=0, minute=0, second=0, microsecond=0)

        while True:
            url = self._get_url(self._web_root, run_utc, self.symbol.broker_symbol_name)
            path = self._get_file_name(self.cache_path, run_utc, self.symbol.broker_symbol_name)
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
                day_data.open_times.data += self._get_hour(run_utc, data).open_times.data
                day_data.open_bids.data += self._get_hour(run_utc, data).open_bids.data
                day_data.open_asks.data += self._get_hour(run_utc, data).open_asks.data
                day_data.volume_bids.data += self._get_hour(run_utc, data).volume_bids.data
                day_data.volume_asks.data += self._get_hour(run_utc, data).volume_asks.data

            run_utc += timedelta(hours=1)
            if run_utc.date() > utc.date():
                break

        return "", self.last_utc, day_data

    def get_first_datetime(self) -> tuple[str, datetime]:
        start_date = datetime(2000, 1, 1)
        end_date = datetime.now()
        error = self.symbol.name + " not found"
        while (end_date - start_date).days > 1:
            mid_date = start_date + (end_date - start_date) / 2
            url = self._get_url(Dukascopy._web_root, mid_date, self.symbol.broker_symbol_name)
            try:
                response = self.requests.get(url, stream=True)
                response.raise_for_status()
                end_date = mid_date
                error = ""
            except requests.RequestException:
                start_date = mid_date

        return error, end_date + timedelta(days=1)

    def get_highest_data_rate(self) -> int:
        return 0  # we (only) can do ticks

    def _get_hour(self, hour_base_time: datetime, data: bytes) -> Bars:
        hour: Bars = Bars(self.symbol.name, 0, 0)

        current_index: int = 0

        while True:
            # Python timestamp is microseconds since 1.1.1970
            # Ducascopy timedelta is milliseconds since hour start
            timestamp: float = struct.unpack_from(">I", data, current_index)[0]

            ask = round(
                struct.unpack_from(">I", data, current_index + 4)[0] * self.symbol.point_size,
                self.symbol.digits,
            )
            bid = round(
                struct.unpack_from(">I", data, current_index + 8)[0] * self.symbol.point_size,
                self.symbol.digits,
            )
            volume_ask = round(
                struct.unpack_from(">f", data, current_index + 12)[0],
                self.symbol.digits,
            )
            volume_bid = round(
                struct.unpack_from(">f", data, current_index + 16)[0],
                self.symbol.digits,
            )

            hour.open_times.data.append(hour_base_time + timedelta(milliseconds=timestamp))
            hour.open_bids.data.append(bid)
            hour.open_asks.data.append(ask)
            hour.volume_bids.data.append(volume_bid)
            hour.volume_asks.data.append(volume_ask)

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
