from talib import MA_Type  # type: ignore
from Api.KitaApiEnums import *
from Api.KitaApi import KitaApi
from Api.CoFu import *
from Api.Constants import *
from Api.Symbol import Symbol
from BrokerProvider.TradePaper import TradePaper
from BrokerProvider.QuoteDukascopy import Dukascopy


class Ultron(KitaApi):
    class TradeType:
        Buy = "Buy"
        Sell = "Sell"

    # History
    # region
    version: str = "Ultron V1.0"
    # V1.0     05.01.24    HMz created
    # endregion

    # Parameter
    # region
    # These parameters can be set by the startup module like MainConsole.py
    # If not set from there, the given default values will be used
    # Initialize parameters and indicators
    period1 = 7
    period2 = 5
    period3 = 32
    period4 = 9
    ma3Ma4DiffMaxPercent = 0.28
    ma1Ma2MinPercent = 0.05
    ma1Ma2MaxPercent = 0.19
    takeProfitPips = 18
    stopLossPips = 103
    volume = 2000
    # endregion

    # Members
    # region
    def __init__(self):
        super().__init__()  # Importatnt, do not delete

    # endregion

    ###################################
    def on_init(self) -> None:

        # request symbol to be used
        error, symbol = self.request_symbol(
            "GBP_USD",  # symbol name
            # datarate is in seconds, 0 means fastetst possible (i.e. Ticks)
            Dukascopy(datarate=Constants.SEC_PER_MINUTE),
            TradePaper(),  # Paper trading
            # If :Normalized is added to America/New_York, 7 hours are added
            # This gives New York 17:00 = midnight so that forex trading runs from Moday 00:00 - Friday 23:59:59
            # (we call this "New York normalized time")
            "America/New_York:Normalized",
        )
        if "" != error:
            return

        self.mMa3ma4DiffMaxVal = self.ma3Ma4DiffMaxPercent / 100
        self.mMa1Ma2MinVal = self.ma1Ma2MinPercent / 100
        self.mMa1Ma2MaxVal = self.ma1Ma2MaxPercent / 100

        self.mDigits = symbol.digits

    ###################################
    def on_start(self, symbol: Symbol) -> None:
        # Members to be re-initialized on each new start
        # region
        # endregion
        self.ma1 = self.LWMA(self.symbol, self.period1, Resolution.Hour, Field.Open)
        self.ma2 = self.LWMA(self.symbol, self.period2, Resolution.Hour, Field.Close)
        self.ma3 = self.SMA(self.symbol, self.period3, Resolution.Hour, Field.Close)
        self.ma4 = self.SMA(self.symbol, self.period4, Resolution.Hour, Field.Close)

    ###################################
    def on_tick(self, symbol: Symbol):
        ma1ma2 = self.ma1.Current.Value - self.ma2.Current.Value
        ma2ma1 = self.ma2.Current.Value - self.ma1.Current.Value
        ma3ma4Diff = abs(self.ma3.Current.Value - self.ma4.Current.Value)

        # Short trade conditions
        if (self.direction in ["Short", "Both"]) and not self.Portfolio.Invested:
            if (
                ma3ma4Diff < self.mMa3ma4DiffMaxVal
                and self.ma3.Current.Value > self.ma1.Current.Value
                and self.ma3.Current.Value > self.ma2.Current.Value
                and self.mBars[0].Bid.Close < self.mBars[1].Bid.Close
                and self.mBars[1].Bid.Close < self.mBars[1].Bid.Open
                and self.mMa1Ma2MinVal < ma1ma2 < self.mMa1Ma2MaxVal
            ):
                self.PlaceOrder(self.TradeType.Sell)

        # Long trade conditions
        if (self.direction in ["Long", "Both"]) and not self.Portfolio.Invested:
            if (
                ma3ma4Diff < self.mMa3ma4DiffMaxVal
                and self.ma3.Current.Value < self.ma1.Current.Value
                and self.ma3.Current.Value < self.ma2.Current.Value
                and self.mBars[0].Ask.Close > self.mBars[1].Ask.Close
                and self.mBars[1].Ask.Close > self.mBars[1].Ask.Open
                and self.mMa1Ma2MinVal < ma2ma1 < self.mMa1Ma2MaxVal
            ):
                self.PlaceOrder(self.TradeType.Buy)


    ###################################
    def on_stop(self):
        print("Done")
