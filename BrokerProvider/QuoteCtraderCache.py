import os
import gzip
import struct
from pytz import UTC
from datetime import datetime
from lzma import LZMADecompressor, FORMAT_AUTO  # type: ignore
from Api.KitaApi import KitaApi, Symbol
from Api.Bars import Bars
from Api.QuoteProvider import QuoteProvider


class QuoteCtraderCache(QuoteProvider):
    provider_name = "cTraderCache"
    _assets_file_name: str = "Assets_Pepperstone_Live.csv"
    _last_hour_base_timestamp: float = 0

    def __init__(self, data_rate: int, parameter: str = ""):
        assets_path = os.path.join("Files", self._assets_file_name)
        QuoteProvider.__init__(self, parameter, assets_path, data_rate)

    def init_symbol(self, api: KitaApi, symbol: Symbol):
        self.api = api
        self.symbol = symbol
        ctrader_path = api.resolve_env_variables(self.parameter)
        self.cache_path = os.path.join(ctrader_path, self.symbol.name, "t1")

    def get_day_at_utc(self, utc: datetime) -> tuple[str, datetime, Bars]:
        day_data: Bars = Bars(self.symbol.name, 0, 0)  # 0 = tick timeframe
        self.last_utc = run_utc = utc.replace(hour=0, minute=0, second=0, microsecond=0)

        path = os.path.join(self.cache_path, run_utc.strftime("%Y%m%d") + ".zticks")
        if os.path.exists(path):
            # Read the compressed file into a byte array
            with gzip.open(path, "rb") as decompressor:
                ba = decompressor.read()

            # Process the byte array to extract data
            source_ndx = 0
            while source_ndx < len(ba):
                # Read epoc milliseconds timestamp (8 bytes long)
                day_data.open_times.data.append(
                    (datetime.fromtimestamp(struct.unpack_from("<q", ba, source_ndx)[0] / 1000.0)).replace(tzinfo=UTC)
                )
                source_ndx += 8

                # Read bid (8 bytes long)
                bid = struct.unpack_from("<q", ba, source_ndx)[0]
                source_ndx += 8

                # Read ask (8 bytes long)
                ask = struct.unpack_from("<q", ba, source_ndx)[0]
                source_ndx += 8

                # Assign bid and ask values, rounding will be done by the caller
                day_data.open_bids.data.append(
                    (
                        bid
                        if bid != 0
                        else (day_data.open_bids.data[-1] if len(day_data.open_bids.data) > 0 else ask)
                    )
                    * self.symbol.point_size
                )
                day_data.open_asks.data.append(
                    (
                        ask
                        if ask != 0
                        else (day_data.open_asks.data[-1] if len(day_data.open_asks.data) > 0 else bid)
                    )
                    * self.symbol.point_size
                )

                day_data.volume_asks.data.append(1)
                day_data.volume_bids.data.append(1)

        return "", self.last_utc, day_data

    def get_first_datetime(self) -> tuple[str, datetime]:
        # List all files in the given path with the specific extension
        files = [file for file in os.listdir(self.cache_path) if file.endswith(".zticks")]

        # Sort the files in ascending order
        files.sort()
        if len(files) == 0:
            return "No files found at " + self.cache_path, datetime.min

        return "", datetime.strptime(files[0].split(".")[0], "%Y%m%d")

    def get_highest_data_rate(self) -> int:
        return 0  # we can do ticks


# end of file
