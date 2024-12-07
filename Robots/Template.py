from math import sqrt
from KitaApiEnums import *
from KitaApi import KitaApi
from Api.CoFu import *
from Constants import *
from KitaApi import Symbol
from talib import MA_Type  # type: ignore

from TradePaper import TradePaper
from QuoteMe import QuoteMe  # type: ignore
from QuoteDukascopy import Dukascopy  # type: ignore
from QuoteTradeMt5 import BrokerMt5  # type: ignore
from QuoteCsv import BrokerCsv  # type: ignore


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
    sqrt252: float = sqrt(252)
    # endregion

    def __init__(self):  # type: ignore
        pass

    ###################################
    def on_start(self) -> None:

        # Members; We do declaration here so members will be reinized by 2nd++ on_start()
        # region
        # endregion

        # Example for
        # mt5_broker =  BrokerMt5("62060378, pepperstone_uk-Demo, tFue0y*akr", data_rate=0)

        error, symbol = self.load_symbol(
            "NZDCAD",
            # data_rate in seconds, 0 means fastetst possible (i.e. Ticks)
            Dukascopy("", data_rate=0),
            # QuoteMe("G:\\Meine Ablage\\TickBars", data_rate=0),
            # Paper trading
            TradePaper(""),
            # If :Normalized is added to America/New_York, 7 hours are added
            # This gives NY 17:00 = midnight so that forex trading runs from Moday 00:00 - Friday 23:59:59
            # (we call this "NY normalized time")
            "America/New_York:Normalized",
        )

        # Example how to use bars
        if "" == error:
            error, m1_bars = symbol.load_bars(Constants.SEC_PER_MINUTE)
            m1_bars.count

    ###################################
    def on_tick(self, symbol: Symbol):
        if symbol.time.date != symbol.prev_time.date:
            print(symbol.time)

    ###################################
    def on_stop(self):
        print("Done")


# End of file
