# Imports
# region
import os
import struct
import pytz
from datetime import datetime, timedelta
from xmlrpc.client import boolean
from typing import Tuple
# the following weired imports are a suggsetion from copilot
# to solve the problem of differences between visual studio editor
# and script runtime. The proble is that the script runtime cannot
# find ..folders because there is no parent module ?!?
try:
    from ..Api.QuoteBar import QuoteBar
    from ..Api.SymbolInfo import SymbolInfo
except:
    from QuoteBar import QuoteBar
    from SymbolInfo import SymbolInfo
# endregion

######################################
class QuoteProvider:
    def __init__(self, TradingClass, symbol_info: SymbolInfo):
        self.bin_settings = TradingClass.bin_settings
        self.symbol_info = symbol_info
        self.file_handle = None

    ######################################
    def __del__(self):
        self.file_handle.close()

    ######################################
    def get_quote_at_date(self, dt) -> Tuple[str, QuoteBar]:
        start_filename = self.bars_filename = os.path.join(
            self.bin_settings.platform_parameter,
            self.symbol_info.name,
            "m1",
            dt.strftime("%Y%m%d") + ".mbars",
        )

        while True:
            self.bars_filename = os.path.join(
                self.bin_settings.platform_parameter,
                self.symbol_info.name,
                "m1",
                dt.strftime("%Y%m%d") + ".mbars",
            )

            if os.path.isfile(self.bars_filename):
                break
            else:
                dt += timedelta(days=1)
                utc_time = datetime.utcnow().astimezone(pytz.utc)
                if dt > utc_time:
                    return "No data found at " + self.bars_filename, None
                else:
                    continue

        if None != self.file_handle:
            self.file_handle.close()

        self.file_handle = open(self.bars_filename, "rb")
        quote = self.read_bar()

        return "", quote

    ######################################
    def get_next_quote(self) -> Tuple[str, QuoteBar]:
        quote = self.read_bar()
        if None == quote:
            self.last_date_time += timedelta(days=1)
            if self.last_date_time > datetime.utcnow().astimezone(pytz.utc):
                return "No more data", None

            return self.get_quote_at_date(self.last_date_time)
        else:
            return "", quote

    ######################################
    def read_bar(self) -> Tuple[str, QuoteBar]:
        quote = QuoteBar()

        dt_data = self.file_handle.read(8)
        if dt_data == b"":
            return None

        unpacked_dt = struct.unpack("<Q", dt_data)[0]
        timestamp = unpacked_dt // 1000

        self.last_date_time = quote.time = datetime.fromtimestamp(timestamp).astimezone(
            pytz.utc
        )
        quote.milli_seconds = unpacked_dt % 1000
        quote.open = round(
            struct.unpack("<L", self.file_handle.read(4))[0]
            * self.symbol_info.tick_size,
            self.symbol_info.digits,
        )
        quote.high = round(
            struct.unpack("<L", self.file_handle.read(4))[0]
            * self.symbol_info.tick_size,
            self.symbol_info.digits,
        )
        quote.low = round(
            struct.unpack("<L", self.file_handle.read(4))[0]
            * self.symbol_info.tick_size,
            self.symbol_info.digits,
        )
        quote.close = round(
            struct.unpack("<L", self.file_handle.read(4))[0]
            * self.symbol_info.tick_size,
            self.symbol_info.digits,
        )
        quote.volume = struct.unpack("<L", self.file_handle.read(4))[0]
        quote.open_ask = round(
            struct.unpack("<L", self.file_handle.read(4))[0]
            * self.symbol_info.tick_size,
            self.symbol_info.digits,
        )
        return quote


# end of file
