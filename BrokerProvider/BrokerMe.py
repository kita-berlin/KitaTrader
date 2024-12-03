import os
import struct
import pytz
from datetime import datetime, timedelta
from KitaApi import QuoteBar, QuoteProvider


class BrokerMe(QuoteProvider):
    def __init__(self, parameter: str, data_rate: int):
        QuoteProvider.__init__(self, parameter, data_rate)
        self.file_handle = None

    def __del__(self):
        if self.file_handle is not None:
            self.file_handle.close()

    def initialize(self, symbol_name: str):
        self.symbol_name = symbol_name

        # parameter: path to me files, assets file name in files directory
        para_split = self.parameter.split(",")
        self.symbol_path = os.path.join(para_split[0], self.symbol_name)
        self.assets_file = para_split[0]

    def get_quote_bar_at_date(self, dt: datetime) -> tuple[str, QuoteBar]:
        self.bars_filename = os.path.join(
            self.symbol_path,
            "m1",
            dt.strftime("%Y%m%d") + ".mbars",
        )

        while True:
            self.bars_filename = os.path.join(
                self.symbol_path,
                "m1",
                dt.strftime("%Y%m%d") + ".mbars",
            )

            if os.path.isfile(self.bars_filename):
                break
            else:
                dt += timedelta(days=1)
                utc_time = datetime.now().astimezone(pytz.utc)
                if dt > utc_time:
                    return "No data found at " + self.bars_filename, None  # type: ignore
                else:
                    continue

        if self.file_handle != None:
            self.file_handle.close()

        self.file_handle = open(self.bars_filename, "rb")
        quote = self.read_quote_bar()

        return "", quote  # type: ignore

    def get_first_quote_bar(self) -> tuple[str, QuoteBar]:
        return None  # type: ignore
        pass

    def get_next_quote_bar(self) -> tuple[str, QuoteBar]:
        quote = self.read_quote_bar()
        if None == quote:  # type: ignore
            self.last_date_time += timedelta(days=1)
            if self.last_date_time > datetime.now().astimezone(pytz.utc):
                return "No more data", None  # type: ignore

            return self.get_quote_bar_at_date(self.last_date_time)
        else:
            return "", quote  # type: ignore

    def read_quote_bar(self) -> tuple[str, QuoteBar]:
        quote = QuoteBar()

        dt_data = self.file_handle.read(8)  # type: ignore
        if dt_data == b"":
            return None  # type: ignore

        unpacked_dt = struct.unpack("<Q", dt_data)[0]
        timestamp = unpacked_dt // 1000

        self.last_date_time = quote.time = datetime.fromtimestamp(timestamp).astimezone(
            pytz.utc
        )
        quote.milli_seconds = unpacked_dt % 1000
        quote.open = round(
            struct.unpack("<L", self.file_handle.read(4))[0]  # type: ignore
            * self.market_values.point_size,
            self.market_values.digits,
        )
        quote.high = round(
            struct.unpack("<L", self.file_handle.read(4))[0]  # type: ignore
            * self.market_values.point_size,
            self.market_values.digits,
        )
        quote.low = round(
            struct.unpack("<L", self.file_handle.read(4))[0]  # type: ignore
            * self.market_values.point_size,
            self.market_values.digits,
        )
        quote.close = round(
            struct.unpack("<L", self.file_handle.read(4))[0]  # type: ignore
            * self.market_values.point_size,
            self.market_values.digits,
        )
        quote.volume = struct.unpack("<L", self.file_handle.read(4))[0]  # type: ignore
        quote.open_spread = round(
            struct.unpack("<L", self.file_handle.read(4))[0]  # type: ignore
            * self.market_values.point_size,
            self.market_values.digits,
        )
        quote.open_spread -= quote.open
        return quote  # type: ignore


# end of file
