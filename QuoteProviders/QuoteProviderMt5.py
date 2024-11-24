import os
import struct
import pandas as pd
from datetime import datetime, timedelta
from xmlrpc.client import boolean
from pytz.tzinfo import static_tz_info
import pytz
import time
import MetaTrader5 as mt5
from Settings import BinSettings
from QuoteBar import QuoteBar
from SymbolInfo import SymbolInfo
from Constants import *
from CoFu import *


class QuoteProvider:
    current_index: int = 0
    broker_tz_info: static_tz_info = None

    def __init__(self, TradingClass, symbol_info: SymbolInfo):
        self.bin_settings = TradingClass.bin_settings
        self.symbol_info = symbol_info

        # set time zone to UTC
        ticks = mt5.copy_ticks_range(
            symbol_info.broker_symbol_name,
            TradingClass.bin_settings.start_dt,
            TradingClass.bin_settings.end_dt,
            mt5.COPY_TICKS_ALL,  # combination of flags defining the type of requested ticks
        )
        print("Ticks received:", len(ticks))

        # create data_frame out of the obtained data
        ticks_frame = pd.data_frame(ticks)
        # convert time in seconds into the datetime format
        ticks_frame["time"] = pd.to_datetime(ticks_frame["time"], unit="s")

        # display data
        # print("\nDisplay dataframe with ticks")
        # print(ticks_frame.head(10))

        # Find UTC offset
        current_tick = mt5.symbol_info_tick(self.symbol_info.broker_symbol_name)
        current_tick_time = datetime.fromtimestamp(currentTick.time)
        utc_offset = int(
            0.5 + (currentTickTime - datetime.utcnow()).total_seconds() / 3600
        )

        # Find all timezones with the same offset
        matching_timezones = []
        for tz in pytz.all_timezones:
            timezone = pytz.timezone(tz)
            # Check if the offset matches (consider daylight saving time)
            if (
                timezone.utcoffset(currentTickTime) is not None
                and timezone.utcoffset(currentTickTime).total_seconds() / 3600
                == utcOffset
            ):
                self.broker_tz_info = timezone
                break

    ######################################
    def __del__(self):
        pass

    ######################################
    def get_utc_from_broker_time(self, brokerDt: datetime) -> datetime:
        loc_broker_dt = self.broker_tz_info.localize(brokerDt)
        return locBrokerDt.astimezone(pytz.utc)

    ######################################
    def get_broker_time_from_utc(self, utc: datetime) -> datetime:
        return utc.astimezone(self.broker_tz_info)

    ######################################
    # def get_quote_at_date(self, dt) -> Tuple[str, QuoteBar]:
    def get1st_quote(self):  # -> str, QuoteBar:
        lenRates: int = 0

        # Info: MT5 uses broker time
        # start datetime is current broker time
        current_tick = mt5.symbol_info_tick(self.symbol_info.name)
        dt_now = self.get_utc_from_broker_time(datetime.fromtimestamp(currentTick.time))

        if self.trading_platform.bin_settings.Platform == Platform.mt5_live:
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

        self.rates = mt5.copy_rates_range(
            self.symbol_info.name,
            mt5.TIMEFRAME_M1,
            self.get_broker_time_from_utc(
                startDt - timedelta(seconds=lookbackTimeSeconds)
            ),
            self.get_broker_time_from_utc(dtNow),
        )

        # debug_mt5_rates_start = datetime.fromtimestamp(self.Rates[0][0])
        # debug_mt5_rates_end = datetime.fromtimestamp(self.Rates[-1][0])

        if self.trading_platform.bin_settings.Platform == Platform.mt5_live:
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
    def get_next_quote(self):  # -> str, QuoteBar:
        if Platform.mt5_backtest == self.trading_platform.bin_settings.Platform:
            self.current_index += 1
            self.current_index = min(self.current_index, len(self.Rates) - 1)

        return "", self.get_current_quote()

    ######################################
    def get_current_quote(self):
        qb = QuoteBar()

        if Platform.mt5_live == self.trading_platform.bin_settings.Platform:
            current_tick = mt5.symbol_info_tick(self.symbol_info.name)
            qb.time = self.get_utc_from_broker_time(
                datetime.fromtimestamp(currentTick.time)
            )
            qb.open = qb.high = qb.low = qb.close = currentTick.bid
            qb.open_ask = currentTick.ask
            qb.milli_seconds = currentTick.time % 1000
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
            qb.open_ask = (
                self.Rates[self.current_index][1]
                + self.Rates[self.current_index][6] * self.symbol_info.tick_size
            )
            real_volume = self.Rates[self.current_index][7]
            qb.is_new_bar = True
        pass

        return qb


# end of file
