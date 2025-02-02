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

    def request_bars(self, timeframe: int, look_back: int = 0):
        if timeframe < Constants.SEC_PER_HOUR:
            if Constants.SEC_PER_MINUTE != timeframe:
                minute_look_back = look_back * timeframe // Constants.SEC_PER_MINUTE
                self.bars_dictonary[Constants.SEC_PER_MINUTE] = Bars(
                    self.name, Constants.SEC_PER_MINUTE, minute_look_back, self.api.DataMode
                )

        elif timeframe < Constants.SEC_PER_DAY:
            if Constants.SEC_PER_HOUR != timeframe:
                hour_look_back = look_back * timeframe // Constants.SEC_PER_HOUR
                self.bars_dictonary[Constants.SEC_PER_HOUR] = Bars(
                    self.name, Constants.SEC_PER_HOUR, hour_look_back, self.api.DataMode
                )

        elif Constants.SEC_PER_DAY != timeframe:
            daily_look_back = look_back * timeframe // Constants.SEC_PER_DAY
            self.bars_dictonary[Constants.SEC_PER_DAY] = Bars(
                self.name, Constants.SEC_PER_HOUR, daily_look_back, self.api.DataMode
            )

        if timeframe in self.bars_dictonary:
            if look_back > self.bars_dictonary[timeframe].look_back:
                self.bars_dictonary[timeframe].look_back = look_back
        else:
            self.bars_dictonary[timeframe] = Bars(self.name, timeframe, look_back, self.api.DataMode)

    def get_bars(self, timeframe: int) -> tuple[str, Bars]:
        if timeframe in self.bars_dictonary:
            return "", self.bars_dictonary[timeframe]
        return "Bars have not been requested in on_init()", Bars(self.name, timeframe, 0, self.api.DataMode)

    def check_historical_data(self):
        # if all data are requested (datetime.min == self.api.AllDataStartUtc), find the first quote
        quote_provider_dt = self.api.AllDataStartUtc
        if datetime.min == self.api.AllDataStartUtc:
            print("Finding first quote of " + self.name)
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

        print(f"Checking {self.name} from " + self.api.AllDataStartUtc.strftime("%d.%m.%Y"))
        run_utc = self.api.AllDataStartUtc.replace(hour=0, minute=0, second=0, microsecond=0)
        one_day_provider_data: Bars = Bars(self.name, 0, 0, self.api.DataMode)
        yesterday_minutes = Bars(self.name, Constants.SEC_PER_MINUTE, 0, self.api.DataMode)

        while True:
            # daily loop
            if not os.path.exists(os.path.join(tick_folder, run_utc.strftime("%Y%m%d_quote.zip"))):
                error, quote_provider_dt, one_day_provider_data = self.quote_provider.get_day_at_utc(run_utc)
                if "No data" == error:
                    return
                else:
                    assert "" == error, error
                self._resize_bars(one_day_provider_data)

                print("Getting " + run_utc.strftime("%d.%m.%Y"))
                daily_tick_csv_buffer = StringIO()
                daily_tick_csv_writer = csv.writer(daily_tick_csv_buffer)
                daily_minute_csv_buffer = StringIO()
                daily_minute_csv_writer = csv.writer(daily_minute_csv_buffer)

                # tick loop
                if "No data" != error:
                    for i in range(one_day_provider_data.count):
                        # use absolute array ...data[i], not rolling windows stuff
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

                        local_minute_bars = Bars(self.name, Constants.SEC_PER_MINUTE, 0, self.api.DataMode)
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
        # Extract the data into a DataFrame
        if 0 == bars.timeframe_seconds:
            data = {
                "open_bids": bars.open_bids.data,
                "high_bids": bars.open_bids.data,
                "low_bids": bars.open_bids.data,
                "close_bids": bars.open_bids.data,
                "volume_bids": bars.volume_bids.data,
                "open_asks": bars.open_asks.data,
                "high_asks": bars.open_asks.data,
                "low_asks": bars.open_asks.data,
                "close_asks": bars.open_asks.data,
                "volume_asks": bars.volume_asks.data,
            }
        else:
            data = {
                "open_bids": bars.open_bids.data,
                "high_bids": bars.high_bids.data,
                "low_bids": bars.low_bids.data,
                "close_bids": bars.close_bids.data,
                "volume_bids": bars.volume_bids.data,
                "open_asks": bars.open_asks.data,
                "high_asks": bars.high_asks.data,
                "low_asks": bars.low_asks.data,
                "close_asks": bars.close_asks.data,
                "volume_asks": bars.volume_asks.data,
            }

        index = pd.to_datetime(bars.open_times.data)  # type: ignore
        df = pd.DataFrame(data, index=index)  # type: ignore

        # Resample the DataFrame
        rule = self._seconds_to_pandas_timeframe(new_timeframe_seconds)  # Resampling rule
        resampled = (
            df.resample(rule)  # type: ignore
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
        new_bars = Bars(bars.symbol_name, new_timeframe_seconds, bars.look_back, self.api.DataMode)

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

        new_bars.count = new_bars.size  # indicate full
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
        if datetime.min == self.api.robot.BacktestStartUtc:
            self.api.robot.BacktestStartUtc = self.api.AllDataStartUtc
            print("Warning: BacktestStartUtc is set to minimum, no lookback data are possible")
        else:
            self.api.robot.BacktestStartUtc = self.api.robot.BacktestStartUtc.replace(tzinfo=UTC)

        if datetime.max == self.api.robot.BacktestEndUtc:
            self.api.robot.BacktestEndUtc = self.api.AllDataEndUtc
        else:
            self.api.robot.BacktestEndUtc = self.api.robot.BacktestEndUtc.replace(tzinfo=UTC)

        # set symbol's local time zones
        self.start_tz_dt = self.api.BacktestStartUtc.astimezone(self.time_zone) + timedelta(
            hours=self.normalized_hours_offset
        )

        self.end_tz_dt = self.api.BacktestEndUtc.astimezone(self.time_zone) + timedelta(
            hours=self.normalized_hours_offset
        )

    def load_datarate_and_bars(self) -> str:
        # find smallest start time of all data rates and bars while loading all bars
        min_start = self.api.AllDataEndUtc
        for timeframe in self.bars_dictonary:
            start = self._load_bars(timeframe, self.api.robot.BacktestStartUtc)
            min_start = min(min_start, start)  # type:ignore

        min_start = min_start.replace(hour=0, minute=0, second=0, microsecond=0)

        # check if tick data rate rquested and load it
        if 0 == self.quote_provider.data_rate:
            # get ticks from quote provider
            self.rate_data = self._load_ticks(min_start)
        else:
            self.rate_data = self.bars_dictonary[self.quote_provider.data_rate]

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

    def _load_ticks(self, start: datetime) -> Bars:
        print(f"\nLoading {self.name} ticks from " + start.strftime("%d.%m.%Y"))
        bars = Bars(self.name, 0, 0, self.api.DataMode)
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
            print("Loading " + self.name + " " + file_date.strftime("%Y-%m-%d"))
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
                            if len(row) > 0:
                                bars.append(
                                    (file_date + timedelta(milliseconds=float(row[0]))).replace(tzinfo=pytz.UTC),
                                    float(row[1]),  # open_bid
                                    0,  # high_bid
                                    0,  # low_bid
                                    0,  # close_bid
                                    1,  # volume_bid
                                    float(row[2]),  # open_ask
                                    0,  # high_ask
                                    0,  # low_ask
                                    0,  # close_ask
                                    1,  # volume_ask
                                )

        return bars

    def _load_bars(self, timeframe: int, start: datetime) -> datetime:
        print(f"\nLoading {self.name} {timeframe} seconds OHLC bars from " + start.strftime("%d.%m.%Y"))
        look_back_start_datetime = datetime.min

        if timeframe < Constants.SEC_PER_HOUR:
            if Constants.SEC_PER_MINUTE == timeframe:
                minute_bars = self._load_minute_bars(timeframe, start)  # load 1 minute bars
                self.bars_dictonary[timeframe] = minute_bars
                look_back_start_datetime = minute_bars.open_times.data[0]  # get absolute 1st element
            else:
                resampled_bars = self._resample(self.bars_dictonary[Constants.SEC_PER_MINUTE], timeframe)
                self.bars_dictonary[timeframe] = resampled_bars
                look_back_start_datetime = resampled_bars.open_times.data[0]  # get absolute 1st element

        elif timeframe < Constants.SEC_PER_DAY:
            if Constants.SEC_PER_HOUR == timeframe:
                look_back_start_datetime = self._load_hour_or_daily_bar(
                    Constants.SEC_PER_HOUR, start
                )  # load 1 hour bars
            else:
                resampled_bars = self._resample(self.bars_dictonary[Constants.SEC_PER_HOUR], timeframe)
                self.bars_dictonary[timeframe] = resampled_bars
                look_back_start_datetime = resampled_bars.open_times.data[0]  # get absolute 1st element

        else:
            if Constants.SEC_PER_DAY == timeframe:
                look_back_start_datetime = self._load_hour_or_daily_bar(
                    Constants.SEC_PER_DAY, start
                )  # load 1 day bars
            else:
                resampled_bars = self._resample(self.bars_dictonary[Constants.SEC_PER_DAY], timeframe)
                self.bars_dictonary[timeframe] = resampled_bars
                look_back_start_datetime = resampled_bars.open_times.data[0]  # get absolute 1st element

        return look_back_start_datetime

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
        bars = self.bars_dictonary[timeframe]
        look_back_run = bars.look_back
        folder = os.path.join(
            self.api.DataPath,
            self.quote_provider.provider_name,
            self.quote_provider.bar_folder[Constants.SEC_PER_MINUTE],
            f"{self.name}",
        )

        # Gather and sort files by date
        file_dates = self._get_sorted_file_dates(folder)

        # Start loading from BacktestStartUtc
        start_idx = bisect_left(file_dates, start)

        # Process additional lookback bars if needed
        while look_back_run > 0:
            start_idx -= 1
            if start_idx < 0:
                break

            zip_path = os.path.join(folder, file_dates[start_idx].strftime("%Y%m%d_quote.zip"))
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
        for file_date in file_dates[start_idx:]:
            print("Loading " + self.name + " " + file_date.strftime("%Y-%m-%d"))
            if file_date > self.api.robot.BacktestEndUtc:
                break

            # Path to the zip file
            zip_path = os.path.join(folder, file_date.strftime("%Y%m%d_quote.zip"))

            with ZipFile(zip_path, "r") as zip_file:
                for csv_file_name in zip_file.namelist():
                    with zip_file.open(csv_file_name) as csv_file:
                        decoded = csv_file.read().decode("utf-8")
                        reader = csv.reader(decoded.splitlines())
                        for row in reader:
                            if len(row) > 0:
                                bars.append(
                                    (file_date + timedelta(milliseconds=int(row[0]))).astimezone(self.time_zone)
                                    + timedelta(hours=self.normalized_hours_offset),
                                    float(row[1]),
                                    float(row[2]),
                                    float(row[3]),
                                    float(row[4]),
                                    float(row[5]),
                                    float(row[6]),
                                    float(row[7]),
                                    float(row[8]),
                                    float(row[9]),
                                    float(row[10]),
                                )

        return bars
        self.bars_dictonary[Constants.SEC_PER_MINUTE]
        return bars.open_times.data[0]  # get absolute 1st element

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
        assert len(lines) > 0
        assert len(lines[0]) > 0

        # Convert the list of strings to datetime objects
        datetime_list = [
            datetime.strptime(line.split(",")[0], "%Y%m%d %H:%M").replace(tzinfo=pytz.UTC) for line in lines
        ]

        # Find the index
        start_index = bisect_left(datetime_list, start)

        # load bars from the start index up to the end datetime
        bars = self.bars_dictonary[timeframe]
        for i in range(start_index - bars.look_back, len(lines)):
            row = lines[i].split(",")
            line_datetime = datetime.strptime(row[0], "%Y%m%d %H:%M").replace(tzinfo=pytz.UTC)
            if line_datetime > self.api.robot.BacktestEndUtc:
                break

            line_datetime = line_datetime.astimezone(self.time_zone) + timedelta(
                hours=self.normalized_hours_offset
            )
            bars.append(
                line_datetime,
                float(row[1]),
                float(row[2]),
                float(row[3]),
                float(row[4]),
                float(row[5]),
                float(row[6]),
                float(row[7]),
                float(row[8]),
                float(row[9]),
                float(row[10]),
            )

        return bars.open_times.data[0]  # get absolute 1st element

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
        self.rate_data.read_index += 1
        if self.rate_data.read_index >= self.rate_data.count:
            return "End reached"

        self.time = self.rate_data.open_times.last(0)
        self.bid = self.rate_data.open_bids.last(0)
        self.ask = self.rate_data.open_asks.last(0)

        self.is_warm_up = self.time < self.start_tz_dt

        for bars in self.bars_dictonary.values():
            if RunMode.RealTime != self.api.robot.RunningMode:
                bars.bars_on_tick(self.time)

            # on real time trading we have to build the bars ourselves
            # create on bars based on ticks ()
            # bars.bars_on_tick_create_bars(self.time, self.bid, self.ask)

        return ""


# end of file