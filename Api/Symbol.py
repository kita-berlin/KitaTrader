from __future__ import annotations
from typing import TYPE_CHECKING
import os
import math
import pytz
import csv

# import pandas as pd
import re
from pathlib import Path
from datetime import datetime, timedelta, tzinfo, timezone
from bisect import bisect_left
from zipfile import ZipFile, ZIP_DEFLATED
from io import StringIO, BytesIO
from Api.KitaApi import RoundingMode
from Api.MarketHours import MarketHours
from Api.QuoteProvider import QuoteProvider
from Api.Constants import Constants
from Api.Bar import Bar
from Api.Bars import Bars
from Api.LeverageTier import LeverageTier

# from numba import jit

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
    tick_data: Bars
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

    def request_bars(self, timeframe: int, look_back: int = 0) -> tuple[str, Bars]:
        if timeframe < Constants.SEC_PER_HOUR:
            if Constants.SEC_PER_MINUTE != timeframe:
                minute_look_back = look_back * timeframe // Constants.SEC_PER_MINUTE
                self.bars_dictonary[Constants.SEC_PER_MINUTE] = Bars(
                    self.name, Constants.SEC_PER_MINUTE, minute_look_back
                )

        elif timeframe < Constants.SEC_PER_DAY:
            if Constants.SEC_PER_HOUR != timeframe:
                hour_look_back = look_back * timeframe // Constants.SEC_PER_HOUR
                self.bars_dictonary[Constants.SEC_PER_HOUR] = Bars(
                    self.name, Constants.SEC_PER_HOUR, hour_look_back
                )

        elif Constants.SEC_PER_DAY != timeframe:
            daily_look_back = look_back * timeframe // Constants.SEC_PER_DAY
            self.bars_dictonary[Constants.SEC_PER_DAY] = Bars(self.name, Constants.SEC_PER_HOUR, daily_look_back)

        if timeframe in self.bars_dictonary:
            if look_back > self.bars_dictonary[timeframe].look_back:
                self.bars_dictonary[timeframe].look_back = look_back
        else:
            self.bars_dictonary[timeframe] = Bars(self.name, timeframe, look_back)
        return "", self.bars_dictonary[timeframe]

    def check_historical_data(self) -> str:
        # format for ticks and minutes: 20140101_quote.zip, microseconds offset is within the file
        # format for hours and days: gbpusd.zip, datetime is within the file
        self._set_tz_awareness()

        # if all data requested, find the first quote
        if datetime.min.replace(tzinfo=timezone.utc) == self.api.AllDataStartUtc:
            print("Finding first quote of " + self.name)
            error, start_dt = self.quote_provider.get_first_datetime()
            assert "" == error, error
            self.api.AllDataStartUtc = start_dt.replace(tzinfo=timezone.utc)

        # define and create folders for the symbol
        tick_folder = minute_folder = hour_folder = daily_folder = ""
        max_data_rate = self.quote_provider.get_highest_data_rate()
        if max_data_rate < Constants.SEC_PER_MINUTE:
            tick_folder = os.path.join(
                self.api.DataPath,
                self.quote_provider.provider_name,
                "tick",
                f"{self.name}",
            )
            os.makedirs(tick_folder, exist_ok=True)

        if max_data_rate < Constants.SEC_PER_HOUR:
            minute_folder = os.path.join(
                self.api.DataPath,
                self.quote_provider.provider_name,
                "minute",
                f"{self.name}",
            )
            os.makedirs(minute_folder, exist_ok=True)

        if max_data_rate < Constants.SEC_PER_DAY:
            hour_folder = os.path.join(
                self.api.DataPath,
                self.quote_provider.provider_name,
                "hour",
            )
            os.makedirs(hour_folder, exist_ok=True)

        daily_folder = os.path.join(
            self.api.DataPath,
            self.quote_provider.provider_name,
            "daily",
        )
        os.makedirs(daily_folder, exist_ok=True)

        print(f"Downloading {self.name} from " + self.api.AllDataStartUtc.strftime("%d.%m.%Y"))
        run_utc = self.api.AllDataStartUtc.replace(hour=0, minute=0, second=0, microsecond=0)
        daily_bar = Bar()
        hour_bar = Bar()
        minute_bar = Bar()
        hour_csv_buffer = StringIO()
        hour_csv_writer = csv.writer(hour_csv_buffer)
        daily_csv_buffer = StringIO()
        daily_csv_writer = csv.writer(daily_csv_buffer)
        last_time: datetime = datetime.min
        last_stamp: int = 0

        while True:
            # daily loop
            error, start_dt, one_day_provider_data = self.quote_provider.get_day_at_utc(run_utc)
            assert "" == error, error

            print(run_utc.strftime("%d.%m.%Y"))
            daily_tick_csv_buffer = StringIO()
            daily_tick_csv_writer = csv.writer(daily_tick_csv_buffer)
            daily_minute_csv_buffer = StringIO()
            daily_minute_csv_writer = csv.writer(daily_minute_csv_buffer)

            for i in range(len(one_day_provider_data.open_times.data)):
                # tick loop
                time = one_day_provider_data.open_times.data[i]
                bid = one_day_provider_data.open_bids.data[i]
                ask = one_day_provider_data.open_asks.data[i]
                volume_bid = one_day_provider_data.volume_bids.data[i]
                volume_ask = one_day_provider_data.volume_asks.data[i]
                milliseconds = (time - run_utc).total_seconds() * 1_000  # Convert to milliseconds

                current_stamp = int(time.timestamp())
                last_stamp = 0 if datetime.min == last_time else int(last_time.timestamp())

                # do day bar aggregation
                if (
                    0 == last_stamp
                    or current_stamp // Constants.SEC_PER_DAY != last_stamp // Constants.SEC_PER_DAY
                ):
                    if 0 != last_stamp:
                        # write daily minute data into the csv/zip file
                        daily_csv_writer.writerow(
                            [
                                daily_bar.open_time.strftime("%Y%m%d %H:%M"),
                                f"{daily_bar.open_bid:.{self.digits}f}",
                                f"{daily_bar.high_bid:.{self.digits}f}",
                                f"{daily_bar.low_bid:.{self.digits}f}",
                                f"{daily_bar.close_bid:.{self.digits}f}",
                                f"{daily_bar.volume_bid:.2f}",
                                f"{daily_bar.open_ask:.{self.digits}f}",
                                f"{daily_bar.high_ask:.{self.digits}f}",
                                f"{daily_bar.low_ask:.{self.digits}f}",
                                f"{daily_bar.close_ask:.{self.digits}f}",
                                f"{daily_bar.volume_ask:.2f}",
                            ]
                        )

                    # add a new empty daily bar
                    daily_bar = Bar(
                        time.replace(hour=0, minute=0, second=0, microsecond=0),
                        bid,
                        bid,
                        bid,
                        bid,
                        volume_bid,
                        ask,
                        ask,
                        ask,
                        ask,
                        volume_ask,
                    )
                else:
                    # update daily bar
                    self._update_bar(daily_bar, bid, ask, volume_bid, volume_ask)

                # do hour bar aggregation
                if (
                    0 == last_stamp
                    or current_stamp // Constants.SEC_PER_HOUR != last_stamp // Constants.SEC_PER_HOUR
                ):
                    if 0 != last_stamp:
                        # write daily minute data into the csv/zip file
                        hour_csv_writer.writerow(
                            [
                                hour_bar.open_time.strftime("%Y%m%d %H:%M"),
                                f"{hour_bar.open_bid:.{self.digits}f}",
                                f"{hour_bar.high_bid:.{self.digits}f}",
                                f"{hour_bar.low_bid:.{self.digits}f}",
                                f"{hour_bar.close_bid:.{self.digits}f}",
                                f"{hour_bar.volume_bid:.2f}",
                                f"{hour_bar.open_ask:.{self.digits}f}",
                                f"{hour_bar.high_ask:.{self.digits}f}",
                                f"{hour_bar.low_ask:.{self.digits}f}",
                                f"{hour_bar.close_ask:.{self.digits}f}",
                                f"{hour_bar.volume_ask:.2f}",
                            ]
                        )

                    # add a new empty hour bar
                    hour_bar = Bar(
                        time.replace(minute=0, second=0, microsecond=0),
                        bid,
                        bid,
                        bid,
                        bid,
                        volume_bid,
                        ask,
                        ask,
                        ask,
                        ask,
                        volume_ask,
                    )
                else:
                    # update hour bar
                    self._update_bar(hour_bar, bid, ask, volume_bid, volume_ask)

                # do minute bar aggregation
                if (
                    0 == last_stamp
                    or current_stamp // Constants.SEC_PER_MINUTE != last_stamp // Constants.SEC_PER_MINUTE
                ):
                    if 0 != last_stamp:
                        # write daily minute data into the csv/zip file
                        daily_minute_csv_writer.writerow(
                            [
                                int(
                                    (
                                        minute_bar.open_time.replace(second=0, microsecond=0) - run_utc
                                    ).total_seconds()
                                    * 1_000
                                ),
                                f"{minute_bar.open_bid:.{self.digits}f}",
                                f"{minute_bar.high_bid:.{self.digits}f}",
                                f"{minute_bar.low_bid:.{self.digits}f}",
                                f"{minute_bar.close_bid:.{self.digits}f}",
                                f"{minute_bar.volume_bid:.2f}",
                                f"{minute_bar.open_ask:.{self.digits}f}",
                                f"{minute_bar.high_ask:.{self.digits}f}",
                                f"{minute_bar.low_ask:.{self.digits}f}",
                                f"{minute_bar.close_ask:.{self.digits}f}",
                                f"{minute_bar.volume_ask:.2f}",
                            ]
                        )

                    # create a new empty minute bar
                    minute_bar = Bar(
                        time.replace(second=0, microsecond=0),
                        bid,
                        bid,
                        bid,
                        bid,
                        volume_bid,
                        ask,
                        ask,
                        ask,
                        ask,
                        volume_ask,
                    )
                else:
                    # update minute bar
                    self._update_bar(minute_bar, bid, ask, volume_bid, volume_ask)

                # write daily tick data into the csv/zip file
                daily_tick_csv_writer.writerow(
                    [int(milliseconds), f"{bid:.{self.digits}f}", f"{ask:.{self.digits}f}"]
                )

                last_time = time
                last_stamp = current_stamp

            # write daily files
            self._write_zip_file(tick_folder, "", run_utc, daily_tick_csv_buffer, "tick")
            self._write_zip_file(minute_folder, "", run_utc, daily_minute_csv_buffer, "minute")

            run_utc += timedelta(days=1)

            if run_utc >= self.api.AllDataEndUtc:
                self._write_zip_file(hour_folder, self.name, datetime.min, hour_csv_buffer, "hour")
                self._write_zip_file(daily_folder, self.name, datetime.min, daily_csv_buffer, "daily")
                break

        return ""

    def load_datarate_and_bars(self) -> str:
        # load requested regular bars
        min_start = datetime.max.replace(tzinfo=timezone.utc)
        for timeframe in self.bars_dictonary:
            start = self._load_bars(timeframe, self.api.robot.BacktestStartUtc)
            min_start = min(min_start, start)  # type:ignore

        # check if ticks for data rate are rquested and load them
        if 0 == self.quote_provider.data_rate:
            # get ticks from quote provider
            error = self._load_ticks(min_start)
            assert "" == error, error
        else:
            self.bar_data = self.bars_dictonary[self.quote_provider.data_rate]

        self.symbol_on_tick()  # set initial time, bid, ask for on_start()
        return ""

    def _update_bar(self, bar: Bar, bid: float, ask: float, volume_bid: float, volume_ask: float):
        bar.high_bid = max(bar.high_bid, bid)
        bar.low_bid = min(bar.low_bid, bid)
        bar.close_bid = bid
        bar.volume_bid += volume_bid
        bar.high_ask = max(bar.high_ask, ask)
        bar.low_ask = min(bar.low_ask, ask)
        bar.close_ask = ask
        bar.volume_ask += volume_ask

    def _write_zip_file(self, folder: str, symbol: str, run_utc: datetime, csv_buffer: StringIO, timeframe: str):
        # Create the zip file in memory
        file = os.path.join(folder, run_utc.strftime("%Y%m%d_quote") if "" == symbol else symbol) + ".zip"
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, mode="w", compression=ZIP_DEFLATED) as zf:
            # Add the CSV file to the zip archive
            zf.writestr(
                run_utc.strftime(
                    (f"%Y%m%d_{self.name}_" + timeframe + "_quote" if "" == symbol else symbol) + ".csv"
                ),
                csv_buffer.getvalue(),
            )

        # Write the zip file to disk
        with open(file, "wb") as f:
            f.write(zip_buffer.getvalue())

    def _load_ticks(self, start: datetime) -> str:
        self.api.AllDataStartUtc = self.api.AllDataStartUtc.replace(tzinfo=timezone.utc)

        print(f"Loading {self.name} ticks ")
        folder = os.path.join(
            self.api.DataPath,
            self.quote_provider.provider_name,
            "tick",
            f"{self.name}",
        )

        # Gather and sort files by date
        file_dates = self._get_sorted_file_dates(folder)

        # Perform binary search
        start_idx = bisect_left(file_dates, start)

        # line example: 79212312,1.65616,1.65694
        # milliseconds offset, bid, ask
        # Loop over the files starting from start_idx
        for file_date in file_dates[start_idx:]:
            print(self.name + " " + file_date.strftime("%Y-%m-%d"))
            if file_date > self.api.robot.BacktestEndUtc:
                break

            # Path to the zip file
            zip_path = os.path.join(folder, file_date.strftime("%Y%m%d_quote.zip"))

            # Unzip and load data from CSV
            with ZipFile(zip_path, "r") as zip_file:
                for csv_file_name in zip_file.namelist():
                    with zip_file.open(csv_file_name) as csv_file:
                        # Read and decode CSV file contents
                        decoded = csv_file.read().decode("utf-8")
                        reader = csv.reader(decoded.splitlines())
                        for row in reader:
                            self.tick_data.open_times.data.append(
                                (file_date + timedelta(milliseconds=int(row[0]))).replace(tzinfo=timezone.utc)
                            )
                            self.tick_data.open_bids.data.append(float(row[1]))
                            self.tick_data.open_asks.data.append(float(row[2]))

        return ""

    def _load_bars(self, timeframe: int, start: datetime) -> datetime:
        print(f"Loading {self.name} {timeframe} seconds OHLC bars")
        start_look_back = datetime.min

        if timeframe < Constants.SEC_PER_HOUR:
            if Constants.SEC_PER_MINUTE == timeframe:
                start_look_back = self._load_minute_bars(start)  # load 1 minute bars
            else:
                start_look_back = self._resample(self.bars_dictonary[Constants.SEC_PER_MINUTE], timeframe)

        elif timeframe < Constants.SEC_PER_DAY:
            if Constants.SEC_PER_HOUR == timeframe:
                start_look_back = self._load_hour_or_daily_bar(Constants.SEC_PER_HOUR, start)  # load 1 hour bars
            else:
                start_look_back = self._resample(self.bars_dictonary[Constants.SEC_PER_HOUR], timeframe)

        else:
            if Constants.SEC_PER_DAY == timeframe:
                start_look_back = self._load_hour_or_daily_bar(Constants.SEC_PER_DAY, start)  # load 1 day bars
            else:
                start_look_back = self._resample(self.bars_dictonary[Constants.SEC_PER_DAY], timeframe)

        return start_look_back

    # @jit()
    def _resample(self, source_bars: Bars, timeframe: int) -> datetime:
        # todo: implement resampling
        return target_bars.open_times.data[0]  # type:ignore

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
            self.api.AllDataEndUtc = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(
                seconds=1
            )
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

    def _load_minute_bars(self, start: datetime) -> datetime:
        bars = self.bars_dictonary[Constants.SEC_PER_MINUTE]
        look_back_run = bars.look_back
        files: list[tuple[datetime, str]] = []
        folder = os.path.join(
            self.api.DataPath,
            self.quote_provider.provider_name,
            self.quote_provider.bar_folder[Constants.SEC_PER_MINUTE],
            f"{self.name}",
        )

        # Gather and sort files by date
        dates = self._get_sorted_file_dates(folder)

        # Start loading from BacktestStartUtc
        start_idx = bisect_left(dates, start)
        # loaded_bars = 0

        # Process additional bars if needed
        while look_back_run > 0 and start_idx > 0:
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

                    if num_bars <= look_back_run:
                        # Load all bars if the file doesn't fulfill look_back
                        look_back_run -= num_bars
                    else:
                        look_back_run = 0  # break

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
                            bars.volume_bids.data.append(int(row[5]))
                            bars.open_asks.data.append(float(row[6]))
                            bars.high_asks.data.append(float(row[7]))
                            bars.low_asks.data.append(float(row[8]))
                            bars.close_asks.data.append(float(row[9]))
                            bars.volume_asks.data.append(int(row[10]))

        return bars.open_times.data[0]

    def _load_hour_or_daily_bar(self, timeframe: int, start: datetime) -> datetime:
        # file name example: gbp_usd.zip
        zipfile = os.path.join(
            self.api.DataPath,
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
            if current_datetime < start:
                low = mid + 1
            elif current_datetime > start:
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
            bars.volume_bids.data.append(int(row[5]))
            bars.open_asks.data.append(float(row[6]))
            bars.high_asks.data.append(float(row[7]))
            bars.low_asks.data.append(float(row[8]))
            bars.close_asks.data.append(float(row[9]))
            bars.volume_asks.data.append(int(row[10]))

        return bars.open_times.data[0]

    def _get_sorted_file_dates(self, folder: str) -> list[datetime]:
        files: list[tuple[datetime, str]] = []
        path = Path(folder)
        if os.path.exists(path):
            for file in path.iterdir():
                match = re.compile(r"(\d{8})_quote\.zip").match(file.name)
                if match:
                    date_str = match.group(1)
                    file_date = datetime.strptime(date_str, "%Y%m%d").replace(tzinfo=pytz.UTC)
                    files.append((file_date, file.name))
            files.sort()

        return [file_date for file_date, _ in files]

    def _get_datetime_from_hour_or_day_zip(self, zip_path: str) -> datetime:
        """
        Opens a zip file, reads the first file inside, and extracts the datetime
        from the first row in the format: `20060320 00:00,...`.

        Parameters:
        - zip_path: Path to the zip file.

        Returns:
        - A `datetime` object representing the date and time from the first row.
        """
        extracted_datetime = datetime.min
        if os.path.exists(zip_path):
            with ZipFile(zip_path, "r") as zf:
                # Get the first file name in the zip archive
                file_list = zf.namelist()
                if not file_list:
                    raise ValueError("The zip archive is empty.")

                first_file = file_list[0]

                # Open the first file and read the content
                with zf.open(first_file) as file:
                    # Read the first line
                    first_line = file.readline().decode("utf-8").strip()
                    # Split the line to extract the datetime
                    date_time_str = first_line.split(",")[0]  # Example: "20060320 00:00"
                    # Convert to a datetime object
                    extracted_datetime = datetime.strptime(date_time_str, "%Y%m%d %H:%M")

        return extracted_datetime

    # @jit()
    def symbol_on_tick(self) -> str:
        bar = Bar()
        self.time = self.bar_data.open_times[self.rate_data_index]
        self.bid = self.bar_data.open_bids[self.rate_data_index]
        self.ask = self.bar_data.open_asks[self.rate_data_index]
        max_size = len(self.bar_data.open_times.data)

        bar.open_time = self.bar_data.open_times[self.rate_data_index]
        bar.open_bid = self.bar_data.open_bids[self.rate_data_index]
        bar.high_bid = self.bar_data.high_bids[self.rate_data_index]
        bar.low_bid = self.bar_data.low_bids[self.rate_data_index]
        bar.close_bid = self.bar_data.close_bids[self.rate_data_index]
        bar.volume_bid = self.bar_data.volume_bids[self.rate_data_index]
        bar.open_ask = self.bar_data.open_asks[self.rate_data_index]
        bar.high_ask = self.bar_data.high_asks[self.rate_data_index]
        bar.low_ask = self.bar_data.low_asks[self.rate_data_index]
        bar.close_ask = self.bar_data.close_asks[self.rate_data_index]
        bar.volume_ask = self.bar_data.volume_asks[self.rate_data_index]

        self.rate_data_index += 1

        if self.rate_data_index >= max_size:
            return "End reached"

        self.is_warm_up = self.time < self.start_tz_dt

        for bars in self.bars_dictonary.values():
            bars.bars_on_tick(self.time, bar)

        return ""


# end of file