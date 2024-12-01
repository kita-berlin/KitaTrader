import os
import struct
import pandas as pd
from datetime import datetime, timedelta
from xmlrpc.client import boolean
from pytz.tzinfo import StaticTzInfo
import pytz
import time
import MetaTrader5 as mt5
from Settings import BinSettings
from QuoteBar import QuoteBar
from SymbolInfo import SymbolInfo
from Constants import *
from CoFu import *


class ProviderQuote:
    current_index: int = 0
    broker_tz_info: StaticTzInfo = None  # type: ignore

    def __init__(self, algo_api, symbol_info: SymbolInfo):
        self.bin_settings = algo_api.bin_settings
        self.symbol_info = symbol_info

        # set time zone to UTC
        ticks = mt5.copy_ticks_range(  # pylint: disable=no-member # type: ignore
            symbol_info.broker_symbol_name,
            algo_api.bin_settings.start_dt,
            algo_api.bin_settings.end_dt,
            mt5.COPY_TICKS_ALL,  # combination of flags defining the type of requested ticks
        )
        print("ticks received:", len(ticks))

        # create data_frame out of the obtained data
        ticks_frame = pd.DataFrame(ticks)
        # convert time in seconds into the datetime format
        ticks_frame["time"] = pd.to_datetime(ticks_frame["time"], unit="s")

        # display data
        # print("\nDisplay dataframe with ticks")
        # print(ticks_frame.head(10))

        # Find UTC offset
        current_tick = mt5.symbol_info_tick(  # pylint: disable=no-member # type: ignore
            self.symbol_info.broker_symbol_name
        )
        current_tick_time = datetime.fromtimestamp(current_tick.time)
        utc_offset = int(
            0.5 + (current_tick_time - datetime.utcnow()).total_seconds() / 3600
        )

        # Find all timezones with the same offset
        matching_timezones = []
        for tz in pytz.all_timezones:
            timezone = pytz.timezone(tz)
            # Check if the offset matches (consider daylight saving time)
            if (
                timezone.utc_offset(current_tick_time) is not None
                and timezone.utc_offset(current_tick_time).total_seconds() / 3600
                == utc_offset
            ):
                self.broker_tz_info = timezone
                break

    ######################################
    def __del__(self):
        pass

    ######################################
    def get_utc_from_broker_time(self, brokerDt: datetime) -> datetime:
        loc_broker_dt = self.broker_tz_info.localize(brokerDt)
        return loc_broker_dt.astimezone(pytz.utc)

    ######################################
    def get_broker_time_from_utc(self, utc: datetime) -> datetime:
        return utc.astimezone(self.broker_tz_info)

    ######################################
    # def get_quote_bar_at_date(self, dt) -> tuple[str, QuoteBar]:
    def get1st_quote(self):  # -> str, QuoteBar:
        lenRates: int = 0

        # Info: MT5 uses broker time
        # start datetime is current broker time
        current_tick = mt5.symbol_info_tick(  # pylint: disable=no-member # type: ignore
            self.symbol_info.name
        )
        dt_now = self.get_utc_from_broker_time(
            datetime.fromtimestamp(current_tick.time)
        )

        if self.trading_platform.bin_settings.platform == Platforms.Mt5Live:
            start_dt = dtNow
        else:
            start_dt = self.trading_platform.get_utc_time_from_local_time(
                self.trading_platform.bin_settings.start_dt
            )

        lookback_time_seconds = (
            2  # double it for weekend gaps etc.
            * (10 + self.trading_platform.bin_settings.bars_in_chart)
            * self.trading_platform.bin_settings.default_timeframe_seconds
        )

        self.rates = mt5.copy_rates_range(  # pylint: disable=no-member # type: ignore
            self.symbol_info.name,
            mt5.TIMEFRAME_M1,
            self.get_broker_time_from_utc(
                startDt - timedelta(seconds=lookbackTimeSeconds)
            ),
            self.get_broker_time_from_utc(dtNow),
        )

        # debug_mt5_rates_start = datetime.fromtimestamp(self.Rates[0][0])
        # debug_mt5_rates_end = datetime.fromtimestamp(self.Rates[-1][0])

        if self.trading_platform.bin_settings.platform == Platforms.Mt5Live:
            self.current_index = len(self.Rates) - 1
        else:
            for i in range(len(self.Rates)):
                bar_time = self.get_utc_from_broker_time(
                    datetime.fromtimestamp(self.Rates[i][0])
                )
                if barTime >= startDt:
                    self.current_index = i
                    break

        return "", self.get_current_quote()

    ######################################
    def get_next_quote_bar(self):  # -> str, QuoteBar:
        if Platforms.Mt5Backtest == self.trading_platform.bin_settings.platform:
            self.current_index += 1
            self.current_index = min(self.current_index, len(self.Rates) - 1)

        return "", self.get_current_quote()

    ######################################
    def get_current_quote(self):
        qb = QuoteBar()

        if Platforms.Mt5Live == self.trading_platform.bin_settings.platform:
            current_tick = mt5.symbol_info_tick(self.symbol_info.name)
            qb.time = self.get_utc_from_broker_time(
                datetime.fromtimestamp(current_tick.time)
            )
            qb.open = qb.high = qb.low = qb.close = current_tick.bid
            qb.open_spread = current_tick.ask
            qb.milli_seconds = current_tick.time % 1000
            time.sleep(0.1)
        else:
            qb.time = self.get_utc_from_broker_time(
                datetime.fromtimestamp(self.Rates[self.current_index][0])
            )
            qb.open = self.Rates[self.current_index][1]
            qb.high = self.Rates[self.current_index][2]
            qb.low = self.Rates[self.current_index][3]
            qb.close = self.Rates[self.current_index][4]
            qb.volume = self.Rates[self.current_index][5]
            qb.open_spread = (
                self.Rates[self.current_index][1]
                + self.Rates[self.current_index][6] * self.symbol_info.point_size
            )
            real_volume = self.Rates[self.current_index][7]
            qb.is_new_bar = True
        pass

        return qb


# end of file
