import os
import gzip
import struct
import pytz
from datetime import datetime, timedelta
from lzma import LZMADecompressor, FORMAT_AUTO  # type: ignore
from Api.KitaApi import KitaApi, Symbol
from Api.Bars import Bars
from Api.KitaApiEnums import BidAsk
from Api.QuoteProvider import QuoteProvider
from Api.KitaApiEnums import *


class QuoteCtraderCache(QuoteProvider):
    provider_name = "cTraderCache"
    _assets_file_name: str = "Assets_Pepperstone_Live.csv"
    _last_hour_base_timestamp: float = 0
    _prev_bid: float = 0
    _prev_ask: float = 0

    def __init__(self, data_rate: int, parameter: str = ""):
        assets_path = os.path.join("Files", self._assets_file_name)
        QuoteProvider.__init__(self, parameter, assets_path, data_rate)

    def init_symbol(self, api: KitaApi, symbol: Symbol):
        self.api = api
        self.symbol = symbol
        ctrader_path = api.resolve_env_variables(self.parameter)
        self.cache_path = os.path.join(ctrader_path, self.symbol.name, "t1")

    def get_day_at_utc(self, utc: datetime) -> tuple[str, datetime, Bars]:
        day_data: Bars = Bars(self.symbol.name, 0, 0, DataMode.Preload)  # 0 = tick timeframe
        self.last_utc = run_utc = utc.replace(hour=0, minute=0, second=0, microsecond=0)

        path = os.path.join(self.cache_path, run_utc.strftime("%Y%m%d") + ".zticks")
        if os.path.exists(path):
            # Read the compressed file into a byte array
            with gzip.open(path, "rb") as decompressor:
                ba = decompressor.read()

            # Process the byte array to extract data
            source_ndx = 0
            self._prev_bid = self._prev_ask = 0
            while source_ndx < len(ba):
                # Read epoc milliseconds timestamp (8 bytes long)
                # Ensure the timestamp is localized to UTC
                # Append the UTC time to day_data.open_times.data
                append_datetime = datetime.fromtimestamp(
                    struct.unpack_from("<q", ba, source_ndx)[0] / 1000.0, tz=pytz.UTC
                )

                source_ndx += 8

                # Read bid (8 bytes long)
                bid = struct.unpack_from("<q", ba, source_ndx)[0] * self.symbol.point_size
                source_ndx += 8

                # Read ask (8 bytes long)
                ask = struct.unpack_from("<q", ba, source_ndx)[0] * self.symbol.point_size
                source_ndx += 8

                # If bid or ask is zero, get the previous value from previous day
                if 0 == self._prev_bid and 0 == bid:
                    self._prev_bid = self._get_prevs_(utc, BidAsk.Bid, ask)

                if 0 == self._prev_ask and 0 == ask:
                    self._prev_ask = self._get_prevs_(utc, BidAsk.Ask, bid)

                # Assign bid and ask values, rounding will be done by the caller
                append_bid = bid if bid != 0 else self._prev_bid
                append_ask = ask if ask != 0 else self._prev_ask

                day_data.append(
                    append_datetime,
                    append_bid,
                    0,
                    0,
                    0,
                    0 if 0 == bid else 1,
                    append_ask,
                    0,
                    0,
                    0,
                    0 if 0 == ask else 1,
                )

                self._prev_bid = append_bid
                self._prev_ask = append_ask
        else:
            return "No data", self.last_utc, day_data

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

    def _get_prevs_(self, utc: datetime, bid_ask: BidAsk, not_0: int) -> float:
        while True:
            utc -= timedelta(days=1)

            path = os.path.join(self.cache_path, utc.strftime("%Y%m%d") + ".zticks")
            assert os.path.exists(path), path + " does not exist"
            # Read the compressed file into a byte array
            with gzip.open(path, "rb") as decompressor:
                ba = decompressor.read()

            # Get the last value of the previous day
            if BidAsk.Bid == bid_ask:
                index = -16
            else:
                index = -8

            source_ndx = len(ba) + index
            while True:
                ret_val = struct.unpack_from("<q", ba, source_ndx)[0] * self.symbol.point_size
                if 0 != ret_val:
                    return ret_val
                source_ndx -= 24
                if source_ndx < 0:
                    assert False, "No non zero " + str(bid_ask)


# end of file
