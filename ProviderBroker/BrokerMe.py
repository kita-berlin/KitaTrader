import os
import struct
import pytz
from datetime import datetime, timedelta
from QuoteBar import QuoteBar
from BrokerProvider import BrokerProvider
from AlgoApi import Symbol


class BrokerMe(BrokerProvider):
    def __init__(self, path: str, assets_file_name: str):
        self.path = path
        self.assets_file_name = assets_file_name
        self.file_handle = None

    def __del__(self):
        if self.file_handle is not None:
            self.file_handle.close()

    def init(self, symbol: Symbol):
        self.symbol = symbol
        self.symbol_path = os.path.join(self.path, symbol.name)
        if not os.path.isdir(self.symbol_path):
            print("Not found: " + self.symbol_path)
            quit()

    def get_quote_at_date(self, dt: datetime) -> tuple[str, QuoteBar]:
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
        quote = self.read_bar()

        return "", quote  # type: ignore

    def get_next_quote(self) -> tuple[str, QuoteBar]:
        quote = self.read_bar()
        if None == quote:  # type: ignore
            self.last_date_time += timedelta(days=1)
            if self.last_date_time > datetime.now().astimezone(pytz.utc):
                return "No more data", None  # type: ignore

            return self.get_quote_at_date(self.last_date_time)
        else:
            return "", quote  # type: ignore

    def read_bar(self) -> tuple[str, QuoteBar]:
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
            * self.symbol.tick_size,
            self.symbol.digits,
        )
        quote.high = round(
            struct.unpack("<L", self.file_handle.read(4))[0]  # type: ignore
            * self.symbol.tick_size,
            self.symbol.digits,
        )
        quote.low = round(
            struct.unpack("<L", self.file_handle.read(4))[0]  # type: ignore
            * self.symbol.tick_size,
            self.symbol.digits,
        )
        quote.close = round(
            struct.unpack("<L", self.file_handle.read(4))[0]  # type: ignore
            * self.symbol.tick_size,
            self.symbol.digits,
        )
        quote.volume = struct.unpack("<L", self.file_handle.read(4))[0]  # type: ignore
        quote.open_ask = round(
            struct.unpack("<L", self.file_handle.read(4))[0]  # type: ignore
            * self.symbol.tick_size,
            self.symbol.digits,
        )
        return quote  # type: ignore

    def update_account(self):
        pass


# end of file
