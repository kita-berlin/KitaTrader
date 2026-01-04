from __future__ import annotations
from typing import TYPE_CHECKING, Any
import os
import math
import pytz
import csv
import pandas as pd
import numpy as np
import re
from pytz import UTC
from pathlib import Path
from datetime import datetime, timedelta, tzinfo
from bisect import bisect_left
from zipfile import ZipFile, ZIP_DEFLATED
from io import StringIO, BytesIO
from Api.KitaApiEnums import *
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
    prev_bid: float = 0
    prev_ask: float = 0
    broker_symbol_name: str = ""
    min_volume: float = 0
    max_volume: float = 0
    lot_size: float = 0
    leverage: float = 0
    time_zone: tzinfo = tzinfo()
    market_data_tz: tzinfo = tzinfo()
    market_open_delta = timedelta()
    market_close_delta = timedelta()
    normalized_hours_offset: int = 0
    swap_long: float = 0
    swap_short: float = 0
    avg_spread: float = 0
    digits: int = 0
    margin_required: float = 0
    min_volume: float = 0
    max_volume: float = 0
    lot_size: float = 0
    commission: float = 0
    symbol_leverage: float = 0
    currency_base: str = ""
    currency_quote: str = ""
    dynamic_leverage: list[LeverageTier] = []
    is_warm_up: bool = True
    _indicator_cache: dict = None  # Cache for indicators by source type for fast lookup
    _last_high_prices: dict = None  # Track last high price per bars for optimization
    _last_low_prices: dict = None  # Track last low price per bars for optimization

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
            # Error - messages removed (use log files)
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

    def request_bars(self, timeframe: int, look_back: int = 0):
        if timeframe < Constants.SEC_PER_HOUR:
            if Constants.SEC_PER_MINUTE != timeframe:
                minute_look_back = look_back * timeframe // Constants.SEC_PER_MINUTE
                self.bars_dictonary[Constants.SEC_PER_MINUTE] = Bars(
                    self.name, Constants.SEC_PER_MINUTE, minute_look_back, symbol=self
                )

        elif timeframe < Constants.SEC_PER_DAY:
            if Constants.SEC_PER_HOUR != timeframe:
                hour_look_back = look_back * timeframe // Constants.SEC_PER_HOUR
                self.bars_dictonary[Constants.SEC_PER_HOUR] = Bars(
                    self.name, Constants.SEC_PER_HOUR, hour_look_back, symbol=self
                )

        elif Constants.SEC_PER_DAY != timeframe:
            daily_look_back = look_back * timeframe // Constants.SEC_PER_DAY
            self.bars_dictonary[Constants.SEC_PER_DAY] = Bars(
                self.name, Constants.SEC_PER_HOUR, daily_look_back, symbol=self
            )

        if timeframe in self.bars_dictonary:
            if look_back > self.bars_dictonary[timeframe].look_back:
                self.bars_dictonary[timeframe].look_back = look_back
        else:
            self.bars_dictonary[timeframe] = Bars(self.name, timeframe, look_back, symbol=self)

    def get_bars(self, timeframe: int) -> tuple[str, Bars]:
        if timeframe in self.bars_dictonary:
            return "", self.bars_dictonary[timeframe]
        return "Bars have not been requested in on_init()", Bars(self.name, timeframe, 0, symbol=self)

    def check_historical_data(self):
        # if all data are requested (datetime.min == self.api.AllDataStartUtc), find the first quote
        quote_provider_dt = self.api.AllDataStartUtc
        if datetime.min == self.api.AllDataStartUtc:
            # Finding first quote - messages removed
            error, quote_provider_dt = self.quote_provider.get_first_datetime()
            assert "" == error, error
        self.api.AllDataStartUtc = quote_provider_dt.replace(tzinfo=UTC)

        # max is up to yesterday because data might not be completed for today
        if datetime.max == self.api.AllDataEndUtc:
            self.api.AllDataEndUtc = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(
                seconds=1
            )
        else:
            self.api.AllDataEndUtc = self.api.AllDataEndUtc.replace(
                hour=0, minute=0, second=0, microsecond=0
            ) + timedelta(days=1)

        self.api.AllDataEndUtc = self.api.AllDataEndUtc.replace(tzinfo=UTC)

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

        # Checking symbol - messages removed
        run_utc = self.api.AllDataStartUtc.replace(hour=0, minute=0, second=0, microsecond=0)
        one_day_provider_data: Bars = Bars(self.name, 0, 0, symbol=self)
        yesterday_minutes = Bars(self.name, Constants.SEC_PER_MINUTE, 0, symbol=self)

        while True:
            # daily loop
            if not os.path.exists(os.path.join(tick_folder, run_utc.strftime("%Y%m%d_quote.zip"))):
                error, quote_provider_dt, one_day_provider_data = self.quote_provider.get_day_at_utc(run_utc)
                if "No data" == error:
                    return
                else:
                    assert "" == error, error
                self._resize_bars(one_day_provider_data)

                # Getting data - messages removed
                daily_tick_csv_buffer = StringIO()
                daily_tick_csv_writer = csv.writer(daily_tick_csv_buffer)
                daily_minute_csv_buffer = StringIO()
                daily_minute_csv_writer = csv.writer(daily_minute_csv_buffer)

                # tick loop
                if "No data" != error:
                    for i in range(one_day_provider_data.count):
                        # use absolute array ...data[i], not rolling windows stuff
                        if 0 == one_day_provider_data.timeframe_seconds:
                            time = one_day_provider_data.open_times_list[i]
                            # Use lists for ticks
                            bid = round(one_day_provider_data.open_bids_list[i], ndigits=self.digits)
                            ask = round(one_day_provider_data.open_asks_list[i], ndigits=self.digits)
                            volume_bid = one_day_provider_data.volume_bids_list[i]
                            volume_ask = one_day_provider_data.volume_asks_list[i]
                        else:
                            # Use Ringbuffer for bars
                            time = one_day_provider_data.open_times.data[i]  # type:ignore
                            bid = round(one_day_provider_data.open_bids.data[i], ndigits=self.digits)
                            ask = round(one_day_provider_data.open_asks.data[i], ndigits=self.digits)
                            volume_bid = one_day_provider_data.volume_bids.data[i]
                            volume_ask = one_day_provider_data.volume_asks.data[i]

                        # write daily tick data into the csv/zip file
                        daily_tick_csv_writer.writerow(
                            [
                                round((time - run_utc).total_seconds() * 1_000.0, 3),  # type:ignore
                                f"{bid:.{self.digits}f}",
                                f"{ask:.{self.digits}f}",
                                f"{volume_bid}",
                                f"{volume_ask}",
                            ]
                        )

                    # write out a daily ticks file; one file for each day
                    # csv file inside the zip file is empty if no ticks are available
                    # we need the zip file to keep track of stored data files
                    self._write_zip_file(tick_folder, run_utc, daily_tick_csv_buffer, "tick")

                    # write out a daily minute file; one file for each day
                    minute_bars = self._resample(one_day_provider_data, Constants.SEC_PER_MINUTE)
                    for i in range(minute_bars.count):
                        daily_minute_csv_writer.writerow(
                            [
                                int(
                                    (
                                        minute_bars.open_times.data[i].replace(second=0, microsecond=0) - run_utc
                                    ).total_seconds()
                                    * 1_000
                                ),
                                f"{minute_bars.open_bids.data[i]:.{self.digits}f}",
                                f"{minute_bars.high_bids.data[i]:.{self.digits}f}",
                                f"{minute_bars.low_bids.data[i]:.{self.digits}f}",
                                f"{minute_bars.close_bids.data[i]:.{self.digits}f}",
                                f"{minute_bars.volume_bids.data[i]:.2f}",
                                f"{minute_bars.open_asks.data[i]:.{self.digits}f}",
                                f"{minute_bars.high_asks.data[i]:.{self.digits}f}",
                                f"{minute_bars.low_asks.data[i]:.{self.digits}f}",
                                f"{minute_bars.close_asks.data[i]:.{self.digits}f}",
                                f"{minute_bars.volume_asks.data[i]:.2f}",
                            ]
                        )
                    self._write_zip_file(minute_folder, run_utc, daily_minute_csv_buffer, "minute")

                    # append to the hours file
                    hour_bars = self._resample(minute_bars, Constants.SEC_PER_HOUR)
                    rows: list[list[Any]] = []
                    for i in range(hour_bars.count):
                        rows.append(  # type:ignore
                            [
                                hour_bars.open_times.data[i].strftime("%Y%m%d %H:%M"),
                                f"{hour_bars.open_bids.data[i]:.{self.digits}f}",
                                f"{hour_bars.high_bids.data[i]:.{self.digits}f}",
                                f"{hour_bars.low_bids.data[i]:.{self.digits}f}",
                                f"{hour_bars.close_bids.data[i]:.{self.digits}f}",
                                f"{hour_bars.volume_bids.data[i]:.2f}",
                                f"{hour_bars.open_asks.data[i]:.{self.digits}f}",
                                f"{hour_bars.high_asks.data[i]:.{self.digits}f}",
                                f"{hour_bars.low_asks.data[i]:.{self.digits}f}",
                                f"{hour_bars.close_asks.data[i]:.{self.digits}f}",
                                f"{hour_bars.volume_asks.data[i]:.2f}",
                            ]
                        )
                    self._append_rows_to_zip(hour_folder, run_utc, self.name, rows)

                    # do the daily bars; a new day starts at market open times, not at UTC :-(
                    is_have_yesterday = True
                    if 0 == yesterday_minutes.count:
                        error, quote_provider_dt, yesterday_ticks = self.quote_provider.get_day_at_utc(
                            run_utc - timedelta(1)
                        )
                        if "No data" == error:
                            is_have_yesterday = False
                        else:
                            assert "" == error, error
                            self._resize_bars(yesterday_ticks)
                            yesterday_minutes = self._resample(yesterday_ticks, Constants.SEC_PER_MINUTE)

                    if (
                        len(minute_bars.open_times.data) > 0
                        and is_have_yesterday
                        and len(yesterday_minutes.open_times.data) > 0
                    ):
                        utc_open_delta = self._local_time_of_day_to_utc(
                            self.market_open_delta, self.market_data_tz
                        )

                        market_open_utc_yesterday = (
                            yesterday_minutes.open_times.data[0].replace(hour=0, minute=0, second=0, microsecond=0)
                            + utc_open_delta
                        )
                        idx_start_yesterday = bisect_left(
                            yesterday_minutes.open_times.data, market_open_utc_yesterday
                        )

                        market_open_utc_today = (
                            minute_bars.open_times.data[0].replace(hour=0, minute=0, second=0, microsecond=0)
                            + utc_open_delta
                        )
                        idx_start_today = bisect_left(minute_bars.open_times.data, market_open_utc_today)

                        local_minute_bars = Bars(self.name, Constants.SEC_PER_MINUTE, 0, symbol=self)
                        local_minute_bars.open_times.data = np.concatenate(
                            (
                                yesterday_minutes.open_times.data[idx_start_yesterday:],
                                minute_bars.open_times.data[:idx_start_today],  # type: ignore
                            )
                        )

                        local_minute_bars.open_times.data -= utc_open_delta  # type: ignore

                        local_minute_bars.open_bids.data = np.concatenate(
                            (
                                yesterday_minutes.open_bids.data[idx_start_yesterday:],
                                minute_bars.open_bids.data[:idx_start_today],
                            )
                        )
                        local_minute_bars.high_bids.data = np.concatenate(
                            (
                                yesterday_minutes.high_bids.data[idx_start_yesterday:],
                                minute_bars.high_bids.data[:idx_start_today],
                            )
                        )
                        local_minute_bars.low_bids.data = np.concatenate(
                            (
                                yesterday_minutes.low_bids.data[idx_start_yesterday:],
                                minute_bars.low_bids.data[:idx_start_today],
                            )
                        )
                        local_minute_bars.close_bids.data = np.concatenate(
                            (
                                yesterday_minutes.close_bids.data[idx_start_yesterday:],
                                minute_bars.close_bids.data[:idx_start_today],
                            )
                        )
                        local_minute_bars.volume_bids.data = np.concatenate(
                            (
                                yesterday_minutes.volume_bids.data[idx_start_yesterday:],
                                minute_bars.volume_bids.data[:idx_start_today],
                            )
                        )

                        local_minute_bars.open_asks.data = np.concatenate(
                            (
                                yesterday_minutes.open_asks.data[idx_start_yesterday:],
                                minute_bars.open_asks.data[:idx_start_today],
                            )
                        )
                        local_minute_bars.high_asks.data = np.concatenate(
                            (
                                yesterday_minutes.high_asks.data[idx_start_yesterday:],
                                minute_bars.high_asks.data[:idx_start_today],
                            )
                        )
                        local_minute_bars.low_asks.data = np.concatenate(
                            (
                                yesterday_minutes.low_asks.data[idx_start_yesterday:],
                                minute_bars.low_asks.data[:idx_start_today],
                            )
                        )
                        local_minute_bars.close_asks.data = np.concatenate(
                            (
                                yesterday_minutes.close_asks.data[idx_start_yesterday:],
                                minute_bars.close_asks.data[:idx_start_today],
                            )
                        )
                        local_minute_bars.volume_asks.data = np.concatenate(
                            (
                                yesterday_minutes.volume_asks.data[idx_start_yesterday:],
                                minute_bars.volume_asks.data[:idx_start_today],
                            )
                        )

                        daily_bars = self._resample(local_minute_bars, Constants.SEC_PER_DAY)
                        daily_bars.open_times.data += utc_open_delta  # type: ignore
                        rows: list[list[Any]] = []
                        for i in range(daily_bars.count):
                            rows.append(  # type:ignore
                                [
                                    daily_bars.open_times.data[i].strftime("%Y%m%d %H:%M"),  # type: ignore
                                    f"{daily_bars.open_bids.data[i]:.{self.digits}f}",
                                    f"{daily_bars.high_bids.data[i]:.{self.digits}f}",
                                    f"{daily_bars.low_bids.data[i]:.{self.digits}f}",
                                    f"{daily_bars.close_bids.data[i]:.{self.digits}f}",
                                    f"{daily_bars.volume_bids.data[i]:.2f}",
                                    f"{daily_bars.open_asks.data[i]:.{self.digits}f}",
                                    f"{daily_bars.high_asks.data[i]:.{self.digits}f}",
                                    f"{daily_bars.low_asks.data[i]:.{self.digits}f}",
                                    f"{daily_bars.close_asks.data[i]:.{self.digits}f}",
                                    f"{daily_bars.volume_asks.data[i]:.2f}",
                                ]
                            )
                        self._append_rows_to_zip(daily_folder, run_utc, self.name, rows)

                    yesterday_minutes = minute_bars

            run_utc += timedelta(days=1)

            # check if end reached
            if run_utc >= self.api.AllDataEndUtc:
                break
        return

    def _local_time_of_day_to_utc(self, local_time_of_day: timedelta, local_tzinfo: tzinfo) -> timedelta:
        """
        Convert a local time of day (timedelta) to its equivalent in UTC.

        Args:
            local_time_of_day (timedelta): Time of day in the local timezone (e.g., 9:30 AM as timedelta).
            local_tzinfo (Union[timezone, pytz.BaseTzInfo]): Timezone information for the local time.

        Returns:
            timedelta: Time of day in UTC as a timedelta.
        """
        # Create a "dummy" local datetime on a reference day
        local_datetime = (
            datetime(2000, 1, 1).replace(hour=0, minute=0, second=0, microsecond=0) + local_time_of_day
        )

        # Localize the datetime to the specified timezone
        localized_datetime = local_tzinfo.localize(local_datetime)  # type:ignore

        # Convert to UTC
        utc_datetime = localized_datetime.astimezone(pytz.utc)  # type:ignore

        # Calculate the UTC time of day as a timedelta
        utc_time_of_day = timedelta(
            hours=utc_datetime.hour,  # type:ignore
            minutes=utc_datetime.minute,  # type:ignore
            seconds=utc_datetime.second,  # type:ignore
            microseconds=utc_datetime.microsecond,  # type:ignore
        )
        return utc_time_of_day

    def _resize_bars(self, bars: Bars):
        bars.open_times.data = np.delete(  # type:ignore
            bars.open_times.data, np.s_[bars.count :]  # type:ignore
        )
        bars.open_bids.data = np.delete(bars.open_bids.data, np.s_[bars.count :])
        bars.open_asks.data = np.delete(bars.open_asks.data, np.s_[bars.count :])
        bars.volume_bids.data = np.delete(bars.volume_bids.data, np.s_[bars.count :])
        bars.volume_asks.data = np.delete(bars.volume_asks.data, np.s_[bars.count :])

    def _resample(self, bars: Bars, new_timeframe_seconds: int) -> Bars:
        # Slice all data arrays to match bars.count (only use valid data, not the full buffer)
        # The data arrays may be larger than bars.count due to buffer pre-allocation
        count = bars.count
        
        # Extract the data into a DataFrame
        if 0 == bars.timeframe_seconds:
            # Tick data: use lists
            data = {
                "open_bids": bars.open_bids_list[:count],
                "high_bids": bars.open_bids_list[:count],
                "low_bids": bars.open_bids_list[:count],
                "close_bids": bars.open_bids_list[:count],
                "volume_bids": bars.volume_bids_list[:count],
                "open_asks": bars.open_asks_list[:count],
                "high_asks": bars.open_asks_list[:count],
                "low_asks": bars.open_asks_list[:count],
                "close_asks": bars.open_asks_list[:count],
                "volume_asks": bars.volume_asks_list[:count],
            }
        else:
            data = {
                "open_bids": bars.open_bids.data[:count],
                "high_bids": bars.high_bids.data[:count],
                "low_bids": bars.low_bids.data[:count],
                "close_bids": bars.close_bids.data[:count],
                "volume_bids": bars.volume_bids.data[:count],
                "open_asks": bars.open_asks.data[:count],
                "high_asks": bars.high_asks.data[:count],
                "low_asks": bars.low_asks.data[:count],
                "close_asks": bars.close_asks.data[:count],
                "volume_asks": bars.volume_asks.data[:count],
            }

        # Convert numpy array of datetime objects to pandas DatetimeIndex
        # bars.open_times.data is a Ringbuffer containing datetime objects
        # We need to convert it properly for pandas
        if count > 0:
            if 0 == bars.timeframe_seconds:
                 # Tick data: use list from open_times_list
                 times_list = bars.open_times_list[:count]
            else:
                 # Bar data: extract from Ringbuffer
                 # Use list comprehension to extract the first 'count' items from Ringbuffer
                 times_list = [bars.open_times.data[i] for i in range(count)]
            
            # Convert to pandas DatetimeIndex
            index = pd.to_datetime(times_list)  # type: ignore
        else:
            # Empty bars - create empty DatetimeIndex
            index = pd.DatetimeIndex([])  # type: ignore
        
        df = pd.DataFrame(data, index=index)  # type: ignore

        # Resample the DataFrame
        rule = self._seconds_to_pandas_timeframe(new_timeframe_seconds)  # Resampling rule
        
        
        origin = 'start_day' # Default
        # Apply to all intraday bars larger than or equal to 1 hour, and Daily bars
        if new_timeframe_seconds >= 3600 and not df.empty:
            first_dt = df.index[0] # UTC timestamp
            ny_tz = pytz.timezone('America/New_York')
            # Convert first timestamp to NY time
            ny_dt = first_dt.astimezone(ny_tz)
            # Anchor to 17:00 NY of the same day
            # Use 17:00 NY of the date of the first tick
            anchor_ny = ny_dt.replace(hour=17, minute=0, second=0, microsecond=0)
            # Convert back to UTC to use as origin
            origin = anchor_ny.astimezone(pytz.UTC)
            # DEBUG: Resample - messages removed

        resampled = (
            df.resample(rule, origin=origin)  # type: ignore
            .apply(
                {
                    "open_bids": "first",
                    "high_bids": "max",
                    "low_bids": "min",
                    "close_bids": "last",
                    "volume_bids": "sum",
                    "open_asks": "first",
                    "high_asks": "max",
                    "low_asks": "min",
                    "close_asks": "last",
                    "volume_asks": "sum",
                }
            )
            .dropna()
        )  # Drop rows with NaN values after resampling

        # Create a new Bars instance for the lower timeframe
        new_bars = Bars(bars.symbol_name, new_timeframe_seconds, bars.look_back, symbol=self)

        # Populate the new Bars instance
        new_bars.open_times.data = np.array(resampled.index.to_pydatetime(), dtype=object)  # type: ignore
        new_bars.open_bids.data = resampled["open_bids"].to_numpy(dtype=np.float64)  # type: ignore
        new_bars.high_bids.data = resampled["high_bids"].to_numpy(dtype=np.float64)  # type: ignore
        new_bars.low_bids.data = resampled["low_bids"].to_numpy(dtype=np.float64)  # type: ignore
        new_bars.close_bids.data = resampled["close_bids"].to_numpy(dtype=np.float64)  # type: ignore
        new_bars.volume_bids.data = resampled["volume_bids"].to_numpy(dtype=np.float64)  # type: ignore
        new_bars.open_asks.data = resampled["open_asks"].to_numpy(dtype=np.float64)  # type: ignore
        new_bars.high_asks.data = resampled["high_asks"].to_numpy(dtype=np.float64)  # type: ignore
        new_bars.low_asks.data = resampled["low_asks"].to_numpy(dtype=np.float64)  # type: ignore
        new_bars.close_asks.data = resampled["close_asks"].to_numpy(dtype=np.float64)  # type: ignore
        new_bars.volume_asks.data = resampled["volume_asks"].to_numpy(dtype=np.float64)  # type: ignore

        new_bars.count = len(resampled)
        # DEBUG: Resampled - messages removed
        return new_bars

    def _append_rows_to_zip(self, folder: str, run_utc: datetime, symbol: str, new_rows: list[list[Any]]) -> None:
        """
        Append rows to a CSV file inside an existing zip archive.

        Args:
            zip_filename (str): The path to the zip file.
            csv_filename (str): The name of the CSV file inside the zip.
            new_rows (list): A list of new rows to append (each row is a list).
        """
        zip_filename = os.path.join(folder, symbol) + ".zip"
        temp_buffer = StringIO()

        csv_filename = symbol + ".csv"
        # Check if the zip file exists
        if os.path.exists(zip_filename):
            with ZipFile(zip_filename, "r") as zipf:
                if csv_filename in zipf.namelist():
                    with zipf.open(zipf.namelist()[0]) as existing_file:
                        # Copy existing rows to a temporary buffer
                        existing_data = existing_file.read().decode("utf-8")
                        temp_buffer.write(existing_data)

        # add new rows to the temporary buffer
        csv_writer = csv.writer(temp_buffer)
        csv_writer.writerows(new_rows)

        # Rewrite the zip file with updated content
        with ZipFile(zip_filename, "w", ZIP_DEFLATED) as zipf:
            # Write the updated CSV content to the zip file
            zipf.writestr(csv_filename, temp_buffer.getvalue())

    def make_time_aware(self):
        # Use internal UTC versions of BacktestStart/BacktestEnd
        if datetime.min == self.api.robot._BacktestStartUtc:
            self.api.robot._BacktestStartUtc = self.api.AllDataStartUtc
        else:
            self.api.robot._BacktestStartUtc = self.api.robot._BacktestStartUtc.replace(tzinfo=UTC)

        if datetime.max == self.api.robot._BacktestEndUtc:
            self.api.robot._BacktestEndUtc = self.api.AllDataEndUtc
        else:
            self.api.robot._BacktestEndUtc = self.api.robot._BacktestEndUtc.replace(tzinfo=UTC)

        # set symbol's local time zones
        self.start_tz_dt = self.api.robot._BacktestStartUtc.astimezone(self.time_zone) + timedelta(
            hours=self.normalized_hours_offset
        )

        self.end_tz_dt = self.api.robot._BacktestEndUtc.astimezone(self.time_zone) + timedelta(
            hours=self.normalized_hours_offset
        )

    def load_datarate_and_bars(self) -> str:
        # check if tick data rate requested and load it first
        # This is needed to resample bars from ticks if bar files don't exist
        min_start = self.api.AllDataStartUtc
        if 0 == self.quote_provider.data_rate:
            # Initialize tick stream - ticks will be processed one at a time, not stored
            self.api._debug_log(f"[load_datarate_and_bars] Initializing tick stream starting from {min_start}")
            self._init_tick_stream(min_start)
            # Get first tick to determine min_start (peek at first tick without consuming it)
            # Save current state
            saved_day = self._tick_current_day
            saved_day_bars = self._tick_day_bars
            saved_day_index = self._tick_day_index
            saved_day_count = self._tick_day_count
            
            # Get first tick
            first_tick = self._get_next_tick()
            if first_tick:
                min_start = first_tick[0]  # time
                self.api._debug_log(f"[load_datarate_and_bars] First tick time: {min_start}")
                # Restore stream state to start from beginning
                self._tick_current_day = saved_day
                self._tick_day_bars = saved_day_bars
                self._tick_day_index = saved_day_index
                self._tick_day_count = saved_day_count
                self._tick_total_processed = 0
            else:
                min_start = self.api.robot._BacktestStartUtc.replace(hour=0, minute=0, second=0, microsecond=0)
                self.api._debug_log(f"[load_datarate_and_bars] No ticks found, using BacktestStart: {min_start}")
            
            if min_start is not None and min_start.tzinfo is None:
                min_start = min_start.replace(tzinfo=pytz.UTC)
        
        # Ensure min_start is not None before proceeding
        if min_start is None:
            min_start = self.api.robot._BacktestStartUtc.replace(hour=0, minute=0, second=0, microsecond=0)
            if min_start.tzinfo is None:
                min_start = min_start.replace(tzinfo=pytz.UTC)
        
    # find smallest start time of all data rates and bars while loading all bars
        for timeframe in list(self.bars_dictonary.keys()):  # Convert to list to avoid RuntimeError during iteration
            start = self._load_bars(timeframe, self.api.AllDataStartUtc)
            if start is None:
                start = datetime.min.replace(tzinfo=pytz.UTC)
            elif start.tzinfo is None and start != datetime.min:
                start = start.replace(tzinfo=pytz.UTC)
            # Ensure min_start is also aware if start is aware, or handle datetime.min
            if min_start is not None and min_start.tzinfo is None and min_start != datetime.min:
                 min_start = min_start.replace(tzinfo=pytz.UTC)
            
            # If one is min (naive) and other is aware, replace min with aware min
            if start == datetime.min: start = start.replace(tzinfo=pytz.UTC)
            if min_start == datetime.min: min_start = min_start.replace(tzinfo=pytz.UTC)

            min_start = min(min_start, start)  # type:ignore

        min_start = min_start.replace(hour=0, minute=0, second=0, microsecond=0)

        # If using bar data rate, set rate_data to that
        if 0 != self.quote_provider.data_rate:
            self.rate_data = self.bars_dictonary[self.quote_provider.data_rate]

        # Initialize indicator cache for fast lookup
        self._build_indicator_cache()

        self.symbol_on_tick()  # set initial time, bid, ask for on_start()
        return ""

    def _write_daily_bar(self, daily_csv_writer, daily_bar: Bar):  # type:ignore
        daily_csv_writer.writerow(  # type:ignore
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

    def _update_bar(self, bar: Bar, bid: float, ask: float, volume_bid: float, volume_ask: float):
        bar.high_bid = max(bar.high_bid, bid)
        bar.low_bid = min(bar.low_bid, bid)
        bar.close_bid = bid
        bar.volume_bid += volume_bid
        bar.high_ask = max(bar.high_ask, ask)
        bar.low_ask = min(bar.low_ask, ask)
        bar.close_ask = ask
        bar.volume_ask += volume_ask

    def _write_zip_file(self, folder: str, run_utc: datetime, csv_buffer: StringIO, timeframe: str):
        # Create the zip file in memory
        file = os.path.join(folder, run_utc.strftime("%Y%m%d_quote")) + ".zip"
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, mode="w", compression=ZIP_DEFLATED) as zf:
            # Add the CSV file to the zip archive
            zf.writestr(
                run_utc.strftime((f"%Y%m%d_{self.name}_" + timeframe + "_quote") + ".csv"),
                csv_buffer.getvalue(),
            )

        # Write the zip file to disk
        with open(file, "wb") as f:
            f.write(zip_buffer.getvalue())

    def _init_tick_stream(self, start: datetime) -> None:
        """
        Initialize tick stream - ticks will be processed one at a time, not stored.
        Creates an iterator that yields ticks from the quote provider.
        """
        # Ensure start is aware
        if start.tzinfo is None:
            start = start.replace(tzinfo=pytz.UTC)
            
        self._tick_current_day = start.replace(hour=0, minute=0, second=0, microsecond=0)
        # For end day, we want to process all ticks up to but not including the end date
        # _BacktestEndUtc is exclusive (e.g., 2025-12-06 00:00:00 means process up to but not including 12/06)
        # So we set _tick_end_day to the end date itself (2025-12-06), and we'll stop when current_day exceeds it
        # This way, we'll process all ticks from 12/05 (the last day before the end date)
        # and stop when current_day becomes 2025-12-06 (which is the end date, so we don't process it)
        self._tick_end_day = self.api.robot._BacktestEndUtc.replace(hour=0, minute=0, second=0, microsecond=0)
        self._tick_day_bars = None
        self._tick_day_index = 0
        self._tick_day_count = 0
        self._tick_total_processed = 0
        
        # Create a minimal rate_data object for compatibility (no storage, just for API)
        # For tick streaming, we don't need to store ticks - just track read_index
        self.rate_data = Bars(self.name, 0, 0, symbol=self)
        self.rate_data.read_index = -1  # Will be incremented before each tick
        self.rate_data.count = 999999999  # Large number so read_index never exceeds it (not used for streaming)
        
        self.api._debug_log(f"[_init_tick_stream] Initialized tick stream from {self._tick_current_day} to {self._tick_end_day}")
    
    def _get_next_tick(self) -> tuple[datetime, float, float, int] | None:
        """
        Get the next tick from the stream.
        Returns (time, bid, ask) or None if no more ticks.
        """
        # Load next day if current day is exhausted
        while self._tick_day_index >= self._tick_day_count:
            # Stop when current_day exceeds end_day (end_day is inclusive, so process all ticks from end_day)
            # _BacktestEndUtc is exclusive (e.g., 2025-12-06 00:00:00 means process up to but not including 12/06)
            # But _tick_end_day is set to 2025-12-06 00:00:00, so we want to process all ticks from 12/06
            # and stop when current_day becomes 2025-12-07 00:00:00
            if self._tick_current_day > self._tick_end_day:
                return None  # No more ticks
            
            # Load next day
            error, _, day_bars = self.quote_provider.get_day_at_utc(self._tick_current_day)
            if error == "":
                self._tick_day_bars = day_bars
                # For tick data, count is length of list (NOT ringbuffer - ticks never go into ringbuffers)
                if hasattr(day_bars, 'open_times_list'):
                    self._tick_day_count = len(day_bars.open_times_list)
                else:
                    # Fallback: should not happen, but handle gracefully
                    self._tick_day_count = 0
                self._tick_day_index = 0
                if self._tick_day_count > 0:
                    self.api._debug_log(f"[_get_next_tick] Loaded {self._tick_day_count} ticks for {self._tick_current_day.strftime('%Y-%m-%d')}")
            else:
                self.api._debug_log(f"[_get_next_tick] Error loading {self._tick_current_day.strftime('%Y-%m-%d')}: {error}")
                self._tick_day_bars = None
                self._tick_day_count = 0
                self._tick_day_index = 0
            
            self._tick_current_day += timedelta(days=1)
        
        # Get tick from current day
        if self._tick_day_bars is None or self._tick_day_index >= self._tick_day_count:
            return None
        
        # Validate indices before accessing (ticks use regular lists, not ringbuffers)
        if (self._tick_day_bars is None or 
            self._tick_day_index >= len(self._tick_day_bars.open_times_list) or
            self._tick_day_index >= len(self._tick_day_bars.open_bids_list) or
            self._tick_day_index >= len(self._tick_day_bars.open_asks_list)):
            # Index out of range - move to next day
            self._tick_day_index = self._tick_day_count  # Force load next day
            return self._get_next_tick()  # Recursively get next tick
        
        # TICKS NEVER GO INTO RINGBUFFERS - use regular lists
        time = self._tick_day_bars.open_times_list[self._tick_day_index]
        bid = self._tick_day_bars.open_bids_list[self._tick_day_index]
        ask = self._tick_day_bars.open_asks_list[self._tick_day_index]
        # Retrieve volume delta stored in volume_bids_list
        vol_delta = int(self._tick_day_bars.volume_bids_list[self._tick_day_index])
        
        # Validate tick data
        import math
        if (time is None or 
            bid is None or math.isnan(bid) or 
            ask is None or math.isnan(ask)):
            # Invalid tick - skip and try next
            self._tick_day_index += 1
            return self._get_next_tick()  # Recursively get next tick
        
        self._tick_day_index += 1
        self._tick_total_processed += 1
        
        return (time, bid, ask, vol_delta)

    def _load_bars(self, timeframe: int, start: datetime) -> datetime:
        # Bars should NOT be preloaded - they will be built incrementally from ticks
        # This function only ensures the Bars object exists and is initialized
        # Actual bar building happens in bars_on_tick() as ticks arrive
        
        # Ensure start is aware
        if start.tzinfo is None:
            start = start.replace(tzinfo=pytz.UTC)
            
        look_back_start_datetime = datetime.min.replace(tzinfo=pytz.UTC)

        # Ensure bars object exists (it should already be created in request_bars)
        if timeframe not in self.bars_dictonary:
            # This should not happen if request_bars was called correctly
                return look_back_start_datetime
        
        # Bars are initialized with count=0 and will be built incrementally from ticks
        # Return the start datetime for reference, but don't preload bars
        return start

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

    def _load_minute_bars(self, timeframe: int, start: datetime) -> Bars:
        # Bars should NOT be preloaded - they will be built incrementally from ticks
        # This function is kept for compatibility but does not preload bars
        # Actual bar building happens in bars_on_tick() as ticks arrive
        
        bars = self.bars_dictonary[timeframe]
        
        # Ensure start is aware
        if start.tzinfo is None:
            start = start.replace(tzinfo=pytz.UTC)
        
        # Bars are initialized with count=0 and will be built incrementally from ticks
        # Return the bars object (with count=0)
        return bars

    def _load_hour_or_daily_bar(self, timeframe: int, start: datetime) -> datetime:
        # Bars should NOT be preloaded - they will be built incrementally from ticks
        # This function is kept for compatibility but does not preload bars
        # Actual bar building happens in bars_on_tick() as ticks arrive
        
        # Ensure start is aware
        if start.tzinfo is None:
            start = start.replace(tzinfo=pytz.UTC)
        
        # Bars are initialized with count=0 and will be built incrementally from ticks
        # Return the start datetime for reference, but don't preload bars
        return start

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
        """
        Internal tick processing workflow:
        1. Get next tick from stream (one at a time, not stored)
        2. Build all bars (bars_on_tick) - new bars go into ring buffers
        3. Calculate dependent indicators first (e.g., SMA before Bollinger Bands)
        4. Calculate independent indicators
        5. When BacktestStart is reached, call user's OnTick
        """
        # Get next tick from stream (one at a time, not stored)
        if 0 == self.quote_provider.data_rate:
            # Tick data: get from stream
            
            
            while True:
                tick_data = self._get_next_tick()
                if tick_data is None:
                    self.api._debug_log(f"[symbol_on_tick] End reached: processed {self._tick_total_processed} ticks")
                    return "End reached"
                
                time, bid, ask, vol_delta = tick_data
                
                
                bars_changed = False
                for bars in self.bars_dictonary.values():
                    previous_count = bars.count
                    previous_read_index = bars.read_index
                    bars.bars_on_tick(time, bid, ask, vol_delta)
                    if bars.count != previous_count or bars.read_index != previous_read_index or bars.is_new_bar:
                        bars_changed = True

                # FILTERING: Check if user's OnTick should be called
                digits = self.digits
                round_factor = 10 ** digits
                bid_rounded = round(bid * round_factor) / round_factor
                ask_rounded = round(ask * round_factor) / round_factor
                prev_bid_rounded = round(self.prev_bid * round_factor) / round_factor if self.prev_bid != 0.0 else 0.0
                prev_ask_rounded = round(self.prev_ask * round_factor) / round_factor if self.prev_ask != 0.0 else 0.0
                
                # Rule: Call OnTick if price changed OR a bar closed
                price_changed = (self.prev_bid == 0.0 and self.prev_ask == 0.0) or \
                                bid_rounded != prev_bid_rounded or ask_rounded != prev_ask_rounded
                
                if not price_changed and not bars_changed:
                    
                    continue
                
                # Tick accepted
                self.time = time
                self.bid = bid
                self.ask = ask
                self.prev_bid = bid
                self.prev_ask = ask
                self.rate_data.read_index += 1
                
                # Log progress
                if self._tick_total_processed % 10000 == 0:
                    self.api._debug_log(f"[symbol_on_tick] Progress: {self._tick_total_processed} ticks, time={self.time}")
                break
        else:
            # Bar data: use DataSeries (not implemented for streaming yet)
            self.rate_data.read_index += 1
            if self.rate_data.read_index >= self.rate_data.count:
                return "End reached"
            self.time = self.rate_data.open_times.last(0)
            self.bid = self.rate_data.open_bids.last(0)
            self.ask = self.rate_data.open_asks.last(0)
            bars_changed = True # Always count as change for bars data

        # Debug first few ticks
        if self.rate_data.read_index < 3:
            self.api._debug_log(f"[symbol_on_tick] Tick {self.rate_data.read_index}: time={self.time}, bid={self.bid}, ask={self.ask}")

        # Safety check: ensure time is not None
        if self.time is None:
            self.api._debug_log(f"[symbol_on_tick] ERROR: time is None for read_index {self.rate_data.read_index}")
            return "End reached"

        # Compare symbol.time (UTC) directly with _BacktestStartUtc (UTC) to avoid timezone conversion issues
        # symbol.time is in UTC from tick data, so compare with UTC start time
        self.is_warm_up = self.time < self.api.robot._BacktestStartUtc

        # Step 2: Calculate indicators in dependency order
        # New Architecture: Skip indicator calculation during INTERNAL chain/warm-up
        # Indicators will be calculated lazily when accessed by user code
        if not self.is_warm_up:
            if bars_changed or self._has_close_indicators():
                self._calculate_indicators_optimized(bars_changed)

        return ""
    
    def _calculate_indicators(self) -> None:
        """
        Calculate all indicators in dependency order for the current bar.
        Only calculates indicators when their source DataSeries has changed:
        - open: only on new bar (is_new_bar)
        - high: only when new high is found (high_changed)
        - low: only when new low is found (low_changed)
        - close: on every tick (always update)
        
        Workflow:
        1. First: Calculate sub-indicators (e.g., SMA, StandardDeviation)
        2. Then: Calculate top-level indicators that depend on sub-indicators (e.g., BollingerBands)
        """
        # Collect all indicators from all bars and DataSeries
        all_indicators = []
        indicator_to_bars = {}  # Map indicator to its bars and source DataSeries
        indicator_to_source = {}  # Map indicator to its source DataSeries type
        
        for bars in self.bars_dictonary.values():
            current_bar_idx = bars.read_index
            
            # Only calculate if we have enough bars
            if current_bar_idx < 0:
                continue
            
            # Check what changed for this bar
            is_new_bar = bars.is_new_bar
            # Check if current price creates a new high or low
            high_changed = bars.high_changed(self.bid)
            low_changed = bars.low_changed(self.bid)
            
            # Collect indicators from all DataSeries, but only if their source has changed
            # Open indicators: only on new bar
            if is_new_bar:
                for data_series in [bars.open_bids, bars.open_asks]:
                    if hasattr(data_series, 'indicator_list') and data_series.indicator_list:
                        for indicator in data_series.indicator_list:
                            if hasattr(indicator, 'periods') and current_bar_idx >= indicator.periods - 1:
                                if indicator not in all_indicators:
                                    all_indicators.append(indicator)
                                    indicator_to_bars[indicator] = (bars, current_bar_idx)
                                    indicator_to_source[indicator] = 'open'
            
            # High indicators: only when new high found
            if high_changed:
                for data_series in [bars.high_bids, bars.high_asks]:
                    if hasattr(data_series, 'indicator_list') and data_series.indicator_list:
                        for indicator in data_series.indicator_list:
                            if hasattr(indicator, 'periods') and current_bar_idx >= indicator.periods - 1:
                                if indicator not in all_indicators:
                                    all_indicators.append(indicator)
                                    indicator_to_bars[indicator] = (bars, current_bar_idx)
                                    indicator_to_source[indicator] = 'high'
            
            # Low indicators: only when new low found
            if low_changed:
                for data_series in [bars.low_bids, bars.low_asks]:
                    if hasattr(data_series, 'indicator_list') and data_series.indicator_list:
                        for indicator in data_series.indicator_list:
                            if hasattr(indicator, 'periods') and current_bar_idx >= indicator.periods - 1:
                                if indicator not in all_indicators:
                                    all_indicators.append(indicator)
                                    indicator_to_bars[indicator] = (bars, current_bar_idx)
                                    indicator_to_source[indicator] = 'low'
            
            # Close indicators: always update (on every tick)
            for data_series in [bars.close_bids, bars.close_asks]:
                if hasattr(data_series, 'indicator_list') and data_series.indicator_list:
                    for indicator in data_series.indicator_list:
                        if hasattr(indicator, 'periods') and current_bar_idx >= indicator.periods - 1:
                            if indicator not in all_indicators:
                                all_indicators.append(indicator)
                                indicator_to_bars[indicator] = (bars, current_bar_idx)
                                indicator_to_source[indicator] = 'close'
        
        # Separate indicators into two groups:
        # 1. Independent indicators (no sub-indicators) or indicators with sub-indicators that need calculation
        # 2. Top-level indicators that depend on sub-indicators
        
        independent_indicators = []
        dependent_indicators = []
        
        for indicator in all_indicators:
            bars, current_bar_idx = indicator_to_bars[indicator]
            
            # Check if indicator has sub-indicators
            has_sub_indicators = False
            sub_indicators = []
            
            # BollingerBands has MovingAverage and StandardDeviation
            if hasattr(indicator, 'MovingAverage') and hasattr(indicator, 'StandardDeviation'):
                has_sub_indicators = True
                sub_indicators.append(indicator.MovingAverage)
                sub_indicators.append(indicator.StandardDeviation)
            
            # StandardDeviation has _movingAverage
            if hasattr(indicator, '_movingAverage'):
                has_sub_indicators = True
                sub_indicators.append(indicator._movingAverage)
            
            if has_sub_indicators:
                dependent_indicators.append((indicator, bars, current_bar_idx, sub_indicators))
            else:
                independent_indicators.append((indicator, bars, current_bar_idx))
        
        # Step 1: Calculate independent indicators first (for current bar)
        # This ensures sub-indicators are ready before dependent indicators use them
        for indicator, bars, current_bar_idx in independent_indicators:
            # Recalculate for current bar since bar data (especially close) may have changed
            indicator.calculate(current_bar_idx)
        
        # Step 2: Calculate dependent indicators (their sub-indicators should already be calculated)
        # But we need to ensure sub-indicators are calculated first for the current bar
        for indicator, bars, current_bar_idx, sub_indicators in dependent_indicators:
            # Calculate sub-indicators first for the current bar
            for sub_indicator in sub_indicators:
                if hasattr(sub_indicator, 'calculate') and hasattr(sub_indicator, 'periods'):
                    if current_bar_idx >= sub_indicator.periods - 1:
                        # Recalculate sub-indicator for current bar
                        sub_indicator.calculate(current_bar_idx)
            
            # Then calculate the top-level indicator for the current bar
            indicator.calculate(current_bar_idx)
    
    def _build_indicator_cache(self) -> None:
        """Build a cache of indicators organized by source type for fast lookup"""
        if self._indicator_cache is None:
            self._indicator_cache = {
                'open': [],  # (indicator, bars, data_series)
                'high': [],
                'low': [],
                'close': []
            }
            self._last_high_prices = {}
            self._last_low_prices = {}
            
            for bars in self.bars_dictonary.values():
                # Cache open indicators
                for data_series in [bars.open_bids, bars.open_asks]:
                    if hasattr(data_series, 'indicator_list') and data_series.indicator_list:
                        for indicator in data_series.indicator_list:
                            self._indicator_cache['open'].append((indicator, bars, data_series))
                
                # Cache high indicators
                for data_series in [bars.high_bids, bars.high_asks]:
                    if hasattr(data_series, 'indicator_list') and data_series.indicator_list:
                        for indicator in data_series.indicator_list:
                            self._indicator_cache['high'].append((indicator, bars, data_series))
                
                # Cache low indicators
                for data_series in [bars.low_bids, bars.low_asks]:
                    if hasattr(data_series, 'indicator_list') and data_series.indicator_list:
                        for indicator in data_series.indicator_list:
                            self._indicator_cache['low'].append((indicator, bars, data_series))
                
                # Cache close indicators
                for data_series in [bars.close_bids, bars.close_asks]:
                    if hasattr(data_series, 'indicator_list') and data_series.indicator_list:
                        for indicator in data_series.indicator_list:
                            self._indicator_cache['close'].append((indicator, bars, data_series))
    
    def _has_close_indicators(self) -> bool:
        """Check if there are any close-based indicators that need updating every tick"""
        return len(self._indicator_cache.get('close', [])) > 0 if self._indicator_cache else False
    
    def _calculate_indicators_optimized(self, bars_changed: bool) -> None:
        """
        Optimized indicator calculation using cached indicator lists.
        Only calculates indicators when their source DataSeries has changed.
        """
        if self._indicator_cache is None:
            self._build_indicator_cache()
        
        indicators_to_calculate = []
        indicator_to_bars = {}
        
        # Collect indicators that need updating based on what changed
        for bars in self.bars_dictonary.values():
            # Use absolute index for indicator calculation
            # count is capped at buffer size, we need total added count
            current_bar_idx = bars._bar_buffer._add_count - 1 if bars._bar_buffer else bars.count - 1
            if current_bar_idx < 0:
                continue
            
            # Open indicators: only on new bar
            if bars.is_new_bar:
                for indicator, cached_bars, data_series in self._indicator_cache.get('open', []):
                    if cached_bars == bars and hasattr(indicator, 'periods') and current_bar_idx >= indicator.periods - 1:
                        if indicator not in indicators_to_calculate:
                            indicators_to_calculate.append(indicator)
                            indicator_to_bars[indicator] = (bars, current_bar_idx)
            
            # High indicators
            for indicator, cached_bars, data_series in self._indicator_cache.get('high', []):
                if cached_bars == bars and hasattr(indicator, 'periods') and current_bar_idx >= indicator.periods - 1:
                    if bars.high_changed(self.bid) or bars.is_new_bar: 
                        if indicator not in indicators_to_calculate:
                            indicators_to_calculate.append(indicator)
                            indicator_to_bars[indicator] = (bars, current_bar_idx)

            # Low indicators
            for indicator, cached_bars, data_series in self._indicator_cache.get('low', []):
                if cached_bars == bars and hasattr(indicator, 'periods') and current_bar_idx >= indicator.periods - 1:
                    if bars.low_changed(self.bid) or bars.is_new_bar: 
                        if indicator not in indicators_to_calculate:
                            indicators_to_calculate.append(indicator)
                            indicator_to_bars[indicator] = (bars, current_bar_idx)

            # Close indicators: always update (on every tick)
            for indicator, cached_bars, data_series in self._indicator_cache.get('close', []):
                if cached_bars == bars and hasattr(indicator, 'periods') and current_bar_idx >= indicator.periods - 1:
                    if indicator not in indicators_to_calculate:
                        indicators_to_calculate.append(indicator)
                        indicator_to_bars[indicator] = (bars, current_bar_idx)
        
        # Separate into dependent and independent indicators
        independent_indicators = []
        dependent_indicators = []
        
        for indicator in indicators_to_calculate:
            bars, current_bar_idx = indicator_to_bars[indicator]
            
            # Check if indicator has sub-indicators
            has_sub_indicators = False
            sub_indicators = []
            
            if hasattr(indicator, 'MovingAverage') and hasattr(indicator, 'StandardDeviation'):
                has_sub_indicators = True
                sub_indicators.append(indicator.MovingAverage)
                sub_indicators.append(indicator.StandardDeviation)
            
            if hasattr(indicator, '_movingAverage'):
                has_sub_indicators = True
                sub_indicators.append(indicator._movingAverage)
            
            if has_sub_indicators:
                dependent_indicators.append((indicator, bars, current_bar_idx, sub_indicators))
            else:
                independent_indicators.append((indicator, bars, current_bar_idx))
        
        # Calculate independent indicators first
        for indicator, bars, current_bar_idx in independent_indicators:
            indicator.calculate(current_bar_idx)
        
        # Calculate dependent indicators (sub-indicators first, then top-level)
        for indicator, bars, current_bar_idx, sub_indicators in dependent_indicators:
            for sub_indicator in sub_indicators:
                if hasattr(sub_indicator, 'calculate') and hasattr(sub_indicator, 'periods'):
                    if current_bar_idx >= sub_indicator.periods - 1:
                        sub_indicator.calculate(current_bar_idx)
            indicator.calculate(current_bar_idx)


# end of file