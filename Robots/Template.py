﻿import talib  # type: ignore
from math import sqrt
from KitaApiEnums import *
from KitaApi import KitaApi, Symbol
from Api.CoFu import *
from Constants import *
from TradePaper import TradePaper
from QuoteMe import QuoteMe  # type: ignore
from QuoteDukascopy import Dukascopy  # type: ignore
from QuoteTradeMt5 import BrokerMt5  # type: ignore
from QuoteCsv import QuoteCsv  # type: ignore


class Template(KitaApi):

    # History
    # region
    version: str = "Template V1.0"
    # V1.0     06.12.24    HMz created
    # endregion

    # Parameter
    # region
    # These parameters can be set by the startup module like MainConsole.py
    # If not set from there, the given default values will be used
    Direction = TradeDirection.Mode1
    # endregion

    # Members
    # region
    def __init__(self):
        super().__init__()  # Importatnt, do not delete

    sqrt252: float = sqrt(252)
    # endregion

    ###################################
    def on_init(self) -> None:

        # default backtest time window; can be overridden befor calling on_start
        self.BacktestStartUtc = datetime.strptime("1.1.2024", "%d.%m.%Y")
        self.BacktestEndUtc = datetime.max  # means latest possible

        # Possible quote_providers
        # datarate is in seconds, 0 means fastetst possible (i.e. Ticks)
        quote_provider = Dukascopy("", datarate=0)
        # quote_provider = QuoteMe("G:\\Meine Ablage\\TickBars", datarate=0),
        # quote_provider = BrokerMt5("62060378, pepperstone_uk-Demo, tFue0y*akr", datarate=0)
        # quote_provider = QuoteCsv("G:\\Meine Ablage", datarate=0)

        # Demo to show all available symbols
        i = 0
        for symbol_name in quote_provider.symbols:
            i = i + 1
            print(str(i) + ": " + symbol_name)

        error, self.nzdcad_symbol = self.load_symbol(
            "NZDCAD",
            quote_provider,
            # Paper trading
            TradePaper(""),
            # If :Normalized is added to America/New_York, 7 hours are added
            # This gives New York 17:00 = midnight so that forex trading runs from Moday 00:00 - Friday 23:59:59
            # (we call this "New York normalized time")
            "America/New_York:Normalized",
        )
        if "" != error:
            print(error)
            exit()

        # Example how to use bars
        error, self.m1_bars = self.nzdcad_symbol.load_bars(Constants.SEC_PER_MINUTE)
        if "" != error:
            print(error)
            exit()

    def on_start(self) -> None:
        # Members to be re-initialized on each new start
        # region
        # endregion

        # example how to use ta-lib
        ta_funcs = talib.get_functions()  # type:ignore
        print(ta_funcs)  # type:ignore

        self.time_period = 1
        talib.SMA(  # type:ignore
            self.m1_bars.close_prices.data[-self.time_period :],  # type:ignore
            timeperiod=self.time_period,
        )[-1]
        pass

        """
        my_sma = self.Sma.Result.Last(0)

        ta_sd = talib.STDDEV(
            self.indi_bars.close_prices.data[-self.time_period :], timeperiod =self.time_period
        )[-1]
        my_sd = self.Sd.Result.Last(0)

        taUpperArray, taMiddleArray, ta_lower_array = talib.BBANDS(
            self.indi_bars.close_prices.data[-self.time_period :],
            timeperiod =self.time_period,
            nbdevup =2,
            nbdevdn =2,
            matype =MA_Type.SMA
        )
        ta_upper = taUpperArray[-1]
        ta_middle = taMiddleArray[-1]
        ta_lower = taLowerArray[-1]

        my_upper = self.bb_indi.Top.Last(0)
        my_middle = self.bb_indi.Main.Last(0)
        my_lower = self.bb_indi.Bottoself.Last(0)
        """

    ###################################
    def on_tick(self, symbol: Symbol):
        if symbol.time.date() != symbol.prev_time.date():
            print(symbol.time.strftime("%Y-%m-%d %H:%M:%S"), ", ", symbol.time.strftime("%A"))

    ###################################
    def on_stop(self):
        print("Done")


# End of file
