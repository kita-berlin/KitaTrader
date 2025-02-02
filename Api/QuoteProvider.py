from __future__ import annotations
from typing import TYPE_CHECKING
import math
import csv
import traceback
import pytz
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from Api.KitaApiEnums import *
from Api.Bars import Bars

if TYPE_CHECKING:
    from Api.KitaApi import KitaApi
    from Api.Symbol import Symbol


class QuoteProvider(ABC):
    api: KitaApi
    symbol: Symbol
    assets_path: str
    provider_name: str
    bar_folder: dict[int, str] = {
        0: "tick",
        60: "minute",
        3600: "hour",
        86400: "daily",
    }
    symbols: list[str] = []

    def __init__(self, parameter: str, assets_path: str, data_rate: int):
        self.parameter = parameter
        self.assets_path = assets_path
        self.data_rate = data_rate
        self.init_market_info(assets_path, None)  # type:ignore

    def init_market_info(self, assets_path: str, symbol: Symbol) -> str:
        error = ""
        try:
            with open(assets_path, newline="") as csvfile:
                reader = csv.reader(csvfile)
                for line in reader:
                    if not line:
                        continue
                    line = [item.strip() for item in line]

                    if "sep" in line[0].lower():
                        continue

                    if line[1] == "Price":
                        continue

                    self.symbols.append(line[0])
                    if line[0] not in symbol.name:  # type:ignore
                        continue

                    if len(line) < 16:
                        return f"{assets_path} has wrong format (not >= 16 columns)"

                    symbol.swap_long = float(line[3])
                    symbol.swap_short = float(line[4])
                    symbol.point_size = float(line[5]) / 10.0
                    symbol.avg_spread = float(line[2]) / symbol.point_size
                    symbol.digits = int(0.5 + math.log10(1 / symbol.point_size))
                    symbol.margin_required = float(line[7])

                    market_time_split = line[8].split("-")
                    market_tzid_split = line[8].split(":")

                    symbol.market_data_tz = pytz.timezone(market_tzid_split[0].strip())
                    if 4 == len(market_tzid_split) and 2 == len(market_time_split):
                        symbol.market_open_delta = timedelta(
                            hours=int(market_tzid_split[1]),
                            minutes=int(market_tzid_split[2].split("-")[0]),
                        )
                        symbol.market_close_delta = timedelta(
                            hours=int(market_time_split[1].split(":")[0]),
                            minutes=int(market_time_split[1].split(":")[1]),
                        )

                    symbol.min_volume = float(line[9])
                    symbol.max_volume = 10000 * symbol.min_volume
                    symbol.commission = float(line[10])
                    symbol.broker_symbol_name = line[11]
                    symbol.symbol_leverage = float(line[12])
                    symbol.lot_size = float(line[13])
                    symbol.currency_base = line[14].strip()
                    symbol.currency_quote = line[15].strip()

        except Exception as ex:
            error = str(ex)
            error += "\n" + traceback.format_exc()

        return error

    @abstractmethod
    def init_symbol(self, api: KitaApi, symbol: Symbol): ...

    @abstractmethod
    def get_day_at_utc(self, utc: datetime) -> tuple[str, datetime, Bars]: ...

    @abstractmethod
    def get_first_datetime(self) -> tuple[str, datetime]: ...

    @abstractmethod
    def get_highest_data_rate(self) -> int: ...


# end of file