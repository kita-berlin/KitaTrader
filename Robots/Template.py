import talib  # type: ignore
import time
import numpy as np
from math import sqrt
from KitaApiEnums import *
from KitaApi import KitaApi, Symbol, Indicators
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
    prev_time: float = 0
    # endregion

    ###################################
    def on_init(self) -> None:

        # 1. Define quote_provider(s)
        # datarate is in seconds, 0 means fastetst possible (i.e. Ticks)
        quote_provider = Dukascopy(datarate=Constants.SEC_PER_MINUTE)
        # quote_provider = BrokerMt5( datarate=0, "62060378, pepperstone_uk-Demo, tFue0y*akr")
        # quote_provider = QuoteCsv(datarate=0, "G:\\Meine Ablage")

        # 2. Define symbol(s); at least one symbol must be defined
        error, self.gbpusd_symbol = self.request_symbol(
            "GBP_USD",
            quote_provider,
            TradePaper(""),  # Paper trading
            # If :Normalized is added to America/New_York, 7 hours are added
            # This gives New York 17:00 = midnight so that forex trading runs from Moday 00:00 - Friday 23:59:59
            # (we call this "New York normalized time")
            "America/New_York:Normalized",
        )
        if "" != error:
            print(error)
            exit()

        # 4. Define one or more bars (optional)
        self.sma_period = 1
        error, self.h1_bars = self.gbpusd_symbol.request_bars(Constants.SEC_PER_HOUR, 0)
        error, self.d1_bars = self.gbpusd_symbol.request_bars(Constants.SEC_PER_DAY, 0)
        error, self.m1_bars = self.gbpusd_symbol.request_bars(Constants.SEC_PER_MINUTE, self.sma_period)

        # 5. Define kita indicators (optional)
        error, self.sma = Indicators.moving_average(
            source=self.m1_bars.close_prices,
            periods=self.sma_period,
            ma_type=MovingAverageType.Simple,
        )

        if "" != error:
            print(error)
            exit()

        # Demo to show all available symbols
        i = 0
        for symbol_name in quote_provider.symbols:
            i = i + 1
            print(str(i) + ": " + symbol_name)

    def on_start(self, symbol: Symbol) -> None:
        # Members to be re-initialized on each new start
        # region
        # endregion

        # example how to use ta-lib
        ta_funcs = talib.get_functions()  # type:ignore
        print(ta_funcs)  # type:ignore

        np_close = np.array(self.m1_bars.close_prices.data)
        ta_sma = talib.SMA(  # type:ignore
            np_close[-self.sma_period :],  # type:ignore
            timeperiod=self.sma_period,
        )[-1]
        print("")

        """
        my_sma = self.Sma.Result.Last(0)

        ta_sd = talib.STDDEV(
            self.indi_bars.close_prices.data[-self.sma_period :], timeperiod =self.sma_period
        )[-1]
        my_sd = self.Sd.Result.Last(0)

        taUpperArray, taMiddleArray, ta_lower_array = talib.BBANDS(
            self.indi_bars.close_prices.data[-self.sma_period :],
            timeperiod =self.sma_period,
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
            diff = time.perf_counter() - self.prev_time
            print(
                symbol.time.strftime("%Y-%m-%d %H:%M:%S"),
                ", ",
                symbol.time.strftime("%A"),
                ", ",
                f"{diff:.3f}",
            )
            self.prev_time = time.perf_counter()

    ###################################
    def on_stop(self):
        print("Done")


# End of file
