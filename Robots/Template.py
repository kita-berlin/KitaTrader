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
    def on_start(self) -> None:

        # Members; We do declaration here so members will be reinized by 2nd++ on_start()
        # region
        # endregion

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

        error, symbol = self.load_symbol(
            "NZDCAD",
            quote_provider,
            # Paper trading
            TradePaper(""),
            # If :Normalized is added to America/New_York, 7 hours are added
            # This gives New York 17:00 = midnight so that forex trading runs from Moday 00:00 - Friday 23:59:59
            # (we call this "New York normalized time")
            "America/New_York:Normalized",
        )

        # Example how to use bars
        if "" == error:
            error, m1_bars = symbol.load_bars(Constants.SEC_PER_MINUTE)
            m1_bars.count

    ###################################
    def on_tick(self, symbol: Symbol):
        if symbol.time.hour != symbol.prev_time.hour:
            print(symbol.time, ", ", symbol.time.strftime("%A"))

    ###################################
    def on_stop(self):
        print("Done")


# End of file
