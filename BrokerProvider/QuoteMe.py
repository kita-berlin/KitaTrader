import os
import struct
import pytz
from datetime import datetime, timedelta
from KitaApi import Quote, QuoteProvider, KitaApi, Symbol


class QuoteMe(QuoteProvider):
    provider_name = "QuoteMe"
    assets_file_name: str = "Assets_Pepperstone_Demo.csv"

    def __init__(self, parameter: str, datarate: int):
        assets_path = os.path.join("Files", self.assets_file_name)
        QuoteProvider.__init__(self, parameter, assets_path, datarate)
        self.file_handle = None

    def __del__(self):
        if self.file_handle is not None:
            self.file_handle.close()

    def init_symbol(self, api: KitaApi, symbol: Symbol):
        self.api = api
        self.symbol = symbol
        self.symbol_path = os.path.join(self.parameter, self.symbol.name)

    def get_day_at_utc(self, dt: datetime) -> tuple[str, Quote]:
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
        quote = self.read_quote()

        return quote

    def find_first_day(self) -> tuple[str, Quote]:
        symbol_timeframe_path = os.path.join(self.symbol_path, "m1")

        # Get all filenames in the directory
        filenames = os.listdir(symbol_timeframe_path)

        # Sort filenames in ascending order
        self.bars_filename = os.path.join(self.symbol_path, "m1", sorted(filenames)[0])

        if self.file_handle != None:
            self.file_handle.close()

        self.file_handle = open(self.bars_filename, "rb")
        quote = self.read_quote()

        return quote

    def get_next_day(self) -> tuple[str, Quote]:
        quote = self.read_quote()
        if None == quote:  # type: ignore
            self.last_utc += timedelta(days=1)
            if self.last_utc > datetime.now().astimezone(pytz.utc):
                return "No more data", None  # type: ignore

            return self.get_day_at_utc(self.last_utc)
        else:
            return quote

    def read_quote(self) -> tuple[str, Quote]:
        quote = Quote()

        dt_data = self.file_handle.read(8)  # type: ignore
        if dt_data == b"":
            return None  # type: ignore

        unpacked_dt = struct.unpack("<Q", dt_data)[0]
        self.last_utc = quote.timestamp = unpacked_dt / 1e3

        quote.bid = round(
            struct.unpack("<L", self.file_handle.read(4))[0]  # type: ignore
            * self.symbol.point_size,
            self.symbol.digits,
        )

        self.file_handle.seek(16)  # type: ignore

        quote.ask = round(
            struct.unpack("<L", self.file_handle.read(4))[0]  # type: ignore
            * self.symbol.point_size,
            self.symbol.digits,
        )
        """
        quote.open_price = round(
            struct.unpack("<L", self.file_handle.read(4))[0]  # type: ignore
            * self.market_values.point_size,
            self.market_values.digits,
        )
        quote.high_price = round(
            struct.unpack("<L", self.file_handle.read(4))[0]  # type: ignore
            * self.market_values.point_size,
            self.market_values.digits,
        )
        quote.low_price = round(
            struct.unpack("<L", self.file_handle.read(4))[0]  # type: ignore
            * self.market_values.point_size,
            self.market_values.digits,
        )
        quote.close_price = round(
            struct.unpack("<L", self.file_handle.read(4))[0]  # type: ignore
            * self.market_values.point_size,
            self.market_values.digits,
        )
        quote.volume = struct.unpack("<L", self.file_handle.read(4))[0]  # type: ignore
        open_ask = (
            struct.unpack("<L", self.file_handle.read(4))[0]  # type: ignore
            * self.market_values.point_size
        )
        quote.open_spread = round(open_ask - quote.open_price, self.market_values.digits)
        """
        return "", quote


# end of file
