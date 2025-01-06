from __future__ import annotations
from typing import TYPE_CHECKING
import os
import math
import pytz
import re
import csv
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta, tzinfo, timezone
from bisect import bisect_left
from zipfile import ZipFile
from Api.KitaApi import QuotesType, RoundingMode
from Api.MarketHours import MarketHours
from Api.QuoteProvider import QuoteProvider
from Api.Constants import Constants
from Api.Bar import Bar
from Api.Bars import Bars
from Api.LeverageTier import LeverageTier

if TYPE_CHECKING:
    from Api.KitaApi import KitaApi
    from Api.TradeProvider import TradeProvider


class Symbol:
    # Members
    # region
    api: KitaApi
    name: str = ""
    bars_dictonary: dict[int, Bars] = {}
    time: datetime = datetime.min
    prev_time: datetime = datetime.min
    start_tz_dt: datetime = datetime.min
    end_tz_dt: datetime = datetime.min
    bid: float = 0
    ask: float = 0
    broker_symbol_name: str = ""
    min_volume: float = 0
    max_volume: float = 0
    lot_size: float = 0
    leverage: float = 0
    time_zone: tzinfo = tzinfo()
    normalized_hours_offset: int = 0
    swap_long: float = 0
    swap_short: float = 0
    avg_spread: float = 0
    digits: int = 0
    margin_required: float = 0
    symbol_tz_id: str = ""
    market_open_time = timedelta()
    market_close_time = timedelta()
    min_volume: float = 0
    max_volume: float = 0
    lot_size: float = 0
    commission: float = 0
    symbol_leverage: float = 0
    currency_base: str = ""
    currency_quote: str = ""
    dynamic_leverage: list[LeverageTier] = []
    tick_data: QuotesType = []
    rate_data_index: int = 0
    is_warm_up: bool = True

    @property
    def point_size(self) -> float:
        return self._point_size

    @point_size.setter
    def point_size(self, value: float):
        self._point_size: float = value
        self.digits = int(0.5 + math.log10(1 / value))

    @property
    def point_value(self) -> float:
        if self.api.account.currency == self.currency_quote:
            return self._point_size * self.lot_size
        else:
            if self.api.account.currency == self.currency_base:
                return 1 / (self._point_size * self.lot_size * self.bid)
        # else:
        # to_do: currency conversion from quote currency to account currency
        return 1

    @property
    def pip_value(self) -> float:
        return self.point_value * 10

    @property
    def pip_size(self) -> float:
        return self.point_size * 10

    @property
    def market_hours(self) -> MarketHours:
        return MarketHours()

    @property
    def spread(self):
        return self.ask - self.bid

    # Define aggregation for OHLCV
    ohlcva_aggregation = {
        "open": "first",  # First open price in the period
        "high": "max",  # Maximum high price in the period
        "low": "min",  # Minimum low price in the period
        "close": "last",  # Last close price in the period
        "volume": "sum",  # Sum of volumes in the period
        "open_ask": "first",  # First open_ask value in the period
    }
    # endregion

    def __init__(
        self,
        api: KitaApi,
        symbol_name: str,
        quote_provider: QuoteProvider,
        trade_provider: TradeProvider,
        str_time_zone: str,
    ):
        self.api = api
        self.name = symbol_name
        self.quote_provider = quote_provider
        self.trade_provider = trade_provider
        tz_split = str_time_zone.split(":")
        self.time_zone = pytz.timezone(tz_split[0])
        self.leverage = self.api.AccountLeverage

        # 7 is the difference between midnight and 17:00 New York time
        if 2 == len(tz_split) and "America/New_York" == tz_split[0] and "Normalized" == tz_split[1]:
            self.normalized_hours_offset = 7

        error = self.quote_provider.init_market_info(
            self.quote_provider.assets_path,
            self,
        )
        if "" != error:
            print(error)
            exit()

    def normalize_volume_in_units(
        self, volume: float, rounding_mode: RoundingMode = RoundingMode.ToNearest
    ) -> float:
        mod = volume % self.min_volume
        floor = volume - mod
        ceiling = floor + self.min_volume
        if RoundingMode.Up == rounding_mode:
            return ceiling

        elif RoundingMode.Down == rounding_mode:
            return floor

        else:
            return floor if volume - floor < ceiling - volume else ceiling

    def quantity_to_volume_in_units(self, quantity: float) -> float:
        return quantity * self.lot_size

    def volume_in_units_to_quantity(self, volume: float) -> float:
        return volume / self.lot_size

    def request_bars(self, timeframe_seconds: int, look_back: int = 0) -> tuple[str, Bars]:
        if timeframe_seconds in self.bars_dictonary:
            if look_back > self.bars_dictonary[timeframe_seconds].look_back:
                self.bars_dictonary[timeframe_seconds].look_back = look_back
        else:
            new_bars = Bars(self.name, timeframe_seconds, look_back)
            self.bars_dictonary[timeframe_seconds] = new_bars
        return "", self.bars_dictonary[timeframe_seconds]

    def load_datarate_and_bars(self) -> str:
        self._set_tz_awareness()

        # check if ticks for data rate are rquested and load them
        if 0 == self.quote_provider.datarate:
            # get ticks from quote provider
            error = self._load_ticks()
            if "" != error:
                return error
        else:
            self.bar_data = self.bars_dictonary[self.quote_provider.datarate]

        # load requested bars
        self._load_bars()

        self.symbol_on_tick()  # set initial time, bid, ask for on_start()
        return ""

    def _load_ticks(self) -> str:
        # find first quote if all data is requested
        if datetime.min.replace(tzinfo=timezone.utc) == self.api.AllDataStartUtc:
            print("Finding first quote of " + self.name)
            error, start_dt, day_data = self.quote_provider.get_first_day()  # type:ignore
            if "" != error:
                return error, None  # type:ignore
            self.api.AllDataStartUtc = start_dt

        self.api.AllDataStartUtc = self.api.AllDataStartUtc.replace(tzinfo=timezone.utc)

        # data read loop
        print(f"Loading {self.name} ticks ")
        files: list[tuple[datetime, str]] = []
        folder = os.path.join(
            self.api.CachePath,
            self.quote_provider.provider_name,
            "tick",
            f"{self.name}",
        )

        # file name example: 20140101_quote.zip
        # yyyyMMdd_quote.zip
        # List and filter files matching the pattern
        for file in Path(folder).iterdir():
            match = re.compile(r"(\d{8})_quote\.zip").match(file.name)
            if match:
                date_str = match.group(1)
                file_date = datetime.strptime(date_str, "%Y%m%d").replace(tzinfo=pytz.UTC)
                files.append((file_date, file.name))

        files.sort()
        # Extract just the dates for binary search
        dates = [file_date for file_date, _ in files]

        # Perform binary search
        start_idx = bisect_left(dates, self.api.robot.BacktestStartUtc)

        # line example: 79212312,1.65616,1.65694
        # milliseconds offset, bid, ask
        # Loop over the files starting from start_idx
        for file_date, file_name in files[start_idx:]:
            print(self.name + " " + file_date.strftime("%Y-%m-%d"))
            if file_date > self.api.robot.BacktestEndUtc:
                break

            # Path to the zip file
            zip_path = os.path.join(folder, file_name)

            # Unzip and load data from CSV
            with ZipFile(zip_path, "r") as zip_file:
                for csv_file_name in zip_file.namelist():
                    with zip_file.open(csv_file_name) as csv_file:
                        # Read and decode CSV file contents
                        decoded = csv_file.read().decode("utf-8")
                        reader = csv.reader(decoded.splitlines())
                        for row in reader:
                            tick = (
                                (file_date + timedelta(milliseconds=int(row[0]))).replace(tzinfo=timezone.utc),
                                float(row[1]),
                                float(row[2]),
                            )
                            self.tick_data.append(tick)

        return ""

    def _load_bars(self):
        for timeframe in self.bars_dictonary:
            print(f"Loading {self.name} {timeframe} seconds OHLC bars")

            if timeframe < Constants.SEC_PER_HOUR:
                self._load_minute_bars()  # load 1 minute bars

                if Constants.SEC_PER_MINUTE != timeframe:
                    self._resample(self.bars_dictonary[Constants.SEC_PER_MINUTE], timeframe)

            elif timeframe < Constants.SEC_PER_DAY:
                self._load_hour_or_daily_bars(Constants.SEC_PER_HOUR)  # load 1 hour bars

                if Constants.SEC_PER_HOUR != timeframe:
                    self._resample(self.bars_dictonary[Constants.SEC_PER_HOUR], timeframe)

            else:
                self._load_hour_or_daily_bars(Constants.SEC_PER_DAY)  # load 1 day bars

                if Constants.SEC_PER_DAY != timeframe:
                    self._resample(self.bars_dictonary[Constants.SEC_PER_DAY], timeframe)

    def _resample(self, source_bars: Bars, second_tf: int):
        pd_tf = self._seconds_to_pandas_timeframe(second_tf)

        # Resample bars to the desired timeframe using pandas resample
        df = pd.DataFrame(
            {
                "time": source_bars.open_times.data,  # Assuming open_times.data is a list of datetime
                "open": source_bars.open_bids.data,
                "high": source_bars.high_bids.data,
                "low": source_bars.low_bids.data,
                "close": source_bars.close_bids.data,
                "volume": source_bars.volume.data,
                "open_ask": source_bars.open_asks.data,  # Include open ask if needed
            }
        )

        # set time as the index
        df["time"] = pd.to_datetime(df["time"])  # type:ignore
        df.set_index("time", inplace=True)  # type:ignore

        # resample
        resampled_df = df.resample(pd_tf).apply(self.ohlcva_aggregation)  # type:ignore

        # save resampled data to the target bars
        target_bars = self.bars_dictonary[second_tf]
        target_bars.open_times.data = resampled_df.index.to_pydatetime().tolist()  # type:ignore
        target_bars.open_bids.data = resampled_df["open"].tolist()
        target_bars.high_bids.data = resampled_df["high"].tolist()
        target_bars.low_bids.data = resampled_df["low"].tolist()
        target_bars.close_bids.data = resampled_df["close"].tolist()
        target_bars.volume.data = resampled_df["volume"].tolist()
        target_bars.open_asks.data = resampled_df["open_ask"].tolist()

    def _seconds_to_pandas_timeframe(self, seconds: int) -> str:
        if seconds % 60 != 0:
            raise ValueError("The seconds value must be a multiple of 60.")

        minutes = seconds // 60

        if minutes < 60:
            return f"{minutes}min"
        else:
            hours = minutes // 60
            if hours < 24:
                return f"{hours}h"
            else:
                days = hours // 24
                return f"{days}D"

    def _set_tz_awareness(self):
        self.api.AllDataStartUtc = self.api.AllDataStartUtc.replace(tzinfo=timezone.utc)

        # max is up to yesterday because data might not be completed for today
        if datetime.max == self.api.AllDataEndUtc:
            self.api.AllDataEndUtc = datetime.now()
        else:
            self.api.AllDataEndUtc += timedelta(days=1)
        self.api.AllDataEndUtc = self.api.AllDataEndUtc.replace(tzinfo=timezone.utc)

        if datetime.max == self.api.BacktestEndUtc:
            self.api.BacktestEndUtc = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            ) - timedelta(seconds=1)
        else:
            self.api.BacktestEndUtc += timedelta(days=1)

        self.api.BacktestStartUtc = self.api.BacktestStartUtc.replace(tzinfo=timezone.utc)
        self.api.BacktestEndUtc = self.api.BacktestEndUtc.replace(tzinfo=timezone.utc)

        # set symbol's local time zones
        self.start_tz_dt = self.api.BacktestStartUtc.astimezone(self.time_zone) + timedelta(
            hours=self.normalized_hours_offset
        )

        self.end_tz_dt = self.api.BacktestEndUtc.astimezone(self.time_zone) + timedelta(
            hours=self.normalized_hours_offset
        )

    def _load_minute_bars(self):
        bars = self.bars_dictonary[Constants.SEC_PER_MINUTE]
        if len(bars.open_times.data) > 0:
            return

        look_back = bars.look_back
        files: list[tuple[datetime, str]] = []
        folder = os.path.join(
            self.api.CachePath,
            self.quote_provider.provider_name,
            self.quote_provider.bar_folder[Constants.SEC_PER_MINUTE],
            f"{self.name}",
        )

        # Gather and sort files by date
        for file in Path(folder).iterdir():
            match = re.compile(r"(\d{8})_quote\.zip").match(file.name)
            if match:
                date_str = match.group(1)
                file_date = datetime.strptime(date_str, "%Y%m%d").replace(tzinfo=pytz.UTC)
                files.append((file_date, file.name))

        files.sort()
        dates = [file_date for file_date, _ in files]

        # Start loading from BacktestStartUtc
        start_idx = bisect_left(dates, self.api.robot.BacktestStartUtc)
        # loaded_bars = 0

        # Process additional bars if needed
        while look_back > 0 and start_idx > 0:
            start_idx -= 1
            file_date, file_name = files[start_idx]
            zip_path = os.path.join(folder, file_name)

            with ZipFile(zip_path, "r") as zip_file:
                csv_file_name = zip_file.namelist()[0]
                with zip_file.open(csv_file_name) as csv_file:
                    decoded = csv_file.read().decode("utf-8")
                    reader = csv.reader(decoded.splitlines())
                    rows = list(reader)  # Read all rows to count bars
                    num_bars = len(rows)

                    if num_bars <= look_back:
                        # Load all bars if the file doesn't fulfill look_back
                        look_back -= num_bars
                    else:
                        look_back = 0  # break

        # Process files starting from BacktestStartUtc
        for file_date, file_name in files[start_idx:]:
            if file_date > self.api.robot.BacktestEndUtc:
                break

            zip_path = os.path.join(folder, file_name)

            with ZipFile(zip_path, "r") as zip_file:
                for csv_file_name in zip_file.namelist():
                    with zip_file.open(csv_file_name) as csv_file:
                        decoded = csv_file.read().decode("utf-8")
                        reader = csv.reader(decoded.splitlines())
                        for row in reader:
                            bars.open_times.data.append(
                                (file_date + timedelta(milliseconds=int(row[0]))).astimezone(self.time_zone)
                                + timedelta(hours=self.normalized_hours_offset)
                            )
                            bars.open_bids.data.append(float(row[1]))
                            bars.high_bids.data.append(float(row[2]))
                            bars.low_bids.data.append(float(row[3]))
                            bars.close_bids.data.append(float(row[4]))
                            bars.volume.data.append(int(row[5]))
                            bars.open_asks.data.append(float(row[6]))

    def _load_hour_or_daily_bars(self, timeframe: int):
        # file name example: gbp_usd.zip
        zipfile = os.path.join(
            self.api.CachePath,
            self.quote_provider.provider_name,
            self.quote_provider.bar_folder[timeframe],
            f"{self.name}.zip",
        )

        with ZipFile(zipfile, "r") as z:
            # Assuming there's only one file in the zip archive
            file_name = z.namelist()[0]
            with z.open(file_name) as f:
                # Read and decode the lines
                lines = f.read().decode("utf-8").strip().split("\n")

        # one line example:
        # date time, bid_open, bid_high, bid_low, bid_close, bid_volume, open_ask, high_ask, low_ask, close_ask, volume_ask
        # 20140101 22:00,1.65616,1.65778,1.65529,1.65778,0,1.65694,1.658,1.65618,1.658,0
        # Perform binary search to find the start line
        low, high = 0, len(lines) - 1
        start_index = 0
        while low <= high:
            mid = (low + high) // 2
            current_datetime = datetime.strptime(lines[mid].split(",")[0], "%Y%m%d %H:%M").replace(
                tzinfo=timezone.utc
            )
            if current_datetime < self.api.robot.BacktestStartUtc:
                low = mid + 1
            elif current_datetime > self.api.robot.BacktestStartUtc:
                high = mid - 1
            else:
                start_index = mid
                break
        if low <= len(lines) - 1 and high < len(lines) - 1:
            start_index = low

        # load bars from the start index up to the end datetime
        bars = self.bars_dictonary[timeframe]
        for i in range(start_index - bars.look_back, len(lines)):
            row = lines[i].split(",")
            line_datetime = datetime.strptime(row[0], "%Y%m%d %H:%M").replace(tzinfo=timezone.utc)
            if line_datetime > self.api.robot.BacktestEndUtc:
                break

            line_datetime = line_datetime.astimezone(self.time_zone) + timedelta(
                hours=self.normalized_hours_offset
            )
            bars.open_times.data.append(line_datetime)
            bars.open_bids.data.append(float(row[1]))
            bars.high_bids.data.append(float(row[2]))
            bars.low_bids.data.append(float(row[3]))
            bars.close_bids.data.append(float(row[4]))
            bars.volume.data.append(int(row[5]))
            bars.open_asks.data.append(float(row[6]))

    def symbol_on_tick(self) -> str:
        if 0 == self.quote_provider.datarate:
            self.time = self.tick_data[self.rate_data_index][0]
            self.bid = self.tick_data[self.rate_data_index][1]
            self.ask = self.tick_data[self.rate_data_index][2]
            max_size = len(self.tick_data)

            bar = Bar()
            bar.open_time = self.tick_data[self.rate_data_index][0]
            bar.open_bid = bar.high_bid = bar.low_bid = bar.close_bid = self.tick_data[self.rate_data_index][1]
            bar.volume_bid += 1
            bar.open_ask = self.tick_data[self.rate_data_index][2]
        else:
            self.time = self.bar_data.open_times[self.rate_data_index]
            self.bid = self.bar_data.open_bids[self.rate_data_index]
            self.ask = self.bar_data.open_asks[self.rate_data_index]
            max_size = len(self.bar_data.open_times.data)

            bar = Bar()
            bar.open_time = self.bar_data.open_times[self.rate_data_index]
            bar.open_bid = self.bar_data.open_bids[self.rate_data_index]
            bar.high_bid = self.bar_data.high_bids[self.rate_data_index]
            bar.low_bid = self.bar_data.low_bids[self.rate_data_index]
            bar.close_bid = self.bar_data.close_bids[self.rate_data_index]
            bar.volume_bid = self.bar_data.volume[self.rate_data_index]
            bar.open_ask = self.bar_data.open_asks[self.rate_data_index]
            # to save performance the following is not implemented (yet)
            # bar.high_ask = self.bar_data.high_asks[self.rate_data_index]
            # bar.low_ask = self.bar_data.low_asks[self.rate_data_index]
            # bar.close_ask = self.bar_data.close_asks[self.rate_data_index]
            # bar.volume_ask = self.bar_data.volume[self.rate_data_index]

        self.rate_data_index += 1

        if self.rate_data_index >= max_size:
            return "End reached"

        self.is_warm_up = self.time < self.start_tz_dt

        for bars in self.bars_dictonary.values():
            bars.bars_on_tick(self.time, bar)

        return ""


# end of file
