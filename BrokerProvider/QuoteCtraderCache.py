import os
import sys
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
        day_data: Bars = Bars(self.symbol.name, 0, 0)  # 0 = tick timeframe
        self.last_utc = run_utc = utc.replace(hour=0, minute=0, second=0, microsecond=0)

        path = os.path.join(self.cache_path, run_utc.strftime("%Y%m%d") + ".zticks")
        if os.path.exists(path):
            date_str = run_utc.strftime("%d.%m.%Y")
            # Loading message goes to debug log, not stdout/stderr
            if hasattr(self, 'api') and self.api:
                self.api._debug_log(f"Loading {date_str}")
            # Read the compressed file into a byte array
            with gzip.open(path, "rb") as decompressor:
                ba = decompressor.read()

            # Process the byte array to extract data
            # Match C# ReadCtDayV2 logic exactly
            source_ndx = 0
            target_ndx = 0  # Track index in day_data (like targetNdx in C#)
            # Use loaderTickSize = 10e-6 (0.00001) like C#
            loader_tick_size = 10e-6  # Same as C# const double loaderTickSize = 10e-6;
            
            # Store bid/ask as integers (like C# Tick2Bid/Tick2Ask arrays)
            tick_bids = []
            tick_asks = []
            tick_times = []
            
            while source_ndx < len(ba):
                # Read epoc milliseconds timestamp (8 bytes long) - same as C#
                timestamp_ms = struct.unpack_from("<q", ba, source_ndx)[0]
                source_ndx += 8
                
                append_datetime = datetime.fromtimestamp(timestamp_ms / 1000.0, tz=pytz.UTC)
                
                # Read bid as int (8 bytes, cast to int like C#: var bid = (int)BitConverter.ToInt64(...))
                bid_int = int(struct.unpack_from("<q", ba, source_ndx)[0])
                source_ndx += 8
                
                # Read ask as int (8 bytes, cast to int like C#: var ask = (int)BitConverter.ToInt64(...))
                ask_int = int(struct.unpack_from("<q", ba, source_ndx)[0])
                source_ndx += 8
                
                # Calculate TickVolume delta using cTrader's logic: 
                # if both Bid and Ask are updated (non-zero in zticks), volume delta is 2, else 1.
                # In cTrader source: return (!backtestingQuote.IsAskHit || !backtestingQuote.IsBidHit) ? 1 : 2;
                vol_delta = 2 if (bid_int > 0 and ask_int > 0) else 1
                
                # Match C# zero handling logic exactly (from ReadCtDayV2):
                # sa.Tick2Bid[targetNdx] = 0 == bid ? (0 == targetNdx ? ask : sa.Tick2Bid[targetNdx - 1]) : bid;
                # sa.Tick2Ask[targetNdx] = 0 == ask ? (0 == targetNdx ? bid : sa.Tick2Ask[targetNdx - 1]) : ask;
                # Note: C# evaluates bid first, then ask, so ask can use the updated bid value
                actual_bid_int = bid_int
                actual_ask_int = ask_int
                
                if actual_bid_int == 0:
                    if target_ndx == 0:
                        actual_bid_int = actual_ask_int  # First tick: use ask if bid is 0
                    else:
                        actual_bid_int = tick_bids[target_ndx - 1]  # Use previous bid from array
                
                if actual_ask_int == 0:
                    if target_ndx == 0:
                        actual_ask_int = actual_bid_int  # First tick: use bid if ask is 0
                    else:
                        actual_ask_int = tick_asks[target_ndx - 1]  # Use previous ask from array
                
                # Store resolved integers
                tick_bids.append(actual_bid_int)
                tick_asks.append(actual_ask_int)
                # Store volume delta in bids list temporarily, we will use it in append loop below
                tick_times.append((append_datetime, vol_delta))
                
                # Duplicate Filtering - REMOVED to match C# TickVolume
                # C# MarketData.GetBars() counts every tick line for volume even if prices are identical
                # Filtering for OnTick is handled in symbol_on_tick instead
                # if target_ndx > 0 and bid_int == tick_bids[-1] and ask_int == tick_asks[-1]:
                #     continue

                # Store as integers (like C# Tick2Bid/Tick2Ask arrays)
                # tick_bids.append(bid_int)
                # tick_asks.append(ask_int)
                # tick_times.append(append_datetime)
                target_ndx += 1
            
            # Now convert integers to doubles using loaderTickSize (like C# dPrice function)
            # dPrice(int iPrice, double tickSize) = tickSize * iPrice
            # Store both integers (for filtering) and floats (for API)
            for i in range(len(tick_times)):
                dt, v_delta = tick_times[i]
                append_bid = tick_bids[i] * loader_tick_size
                append_ask = tick_asks[i] * loader_tick_size
                
                day_data.append(
                    dt,
                    append_bid,
                    0, 0, 0,
                    float(v_delta),  # Store TickVolume delta in volume_bid field
                    append_ask,
                    0, 0, 0,
                    float(v_delta),  # Store TickVolume delta in volume_ask field
                )
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
