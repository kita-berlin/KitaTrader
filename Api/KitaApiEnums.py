from enum import Enum


class TradeStates(Enum):
    Long = 0
    Short = 1
    Flat = 2


class HighLow(Enum):
    High = 0
    Low = 1


class TradeAction(Enum):
    Open = 0
    Close = 1


class BidAsk(Enum):
    Bid = 0
    Ask = 1


class ArithmeticOperators(Enum):
    Min = 0
    Max = 1
    Greater = 2
    GreaterEqual = 3
    Less = 4
    LessEqual = 5
    Equal = 6


class ProfitMode(Enum):
    Lots = 0
    LotsPro10k = 1
    ProfitPercent = 2
    ProfitAmmount = 3
    RiskConstant = 4
    RiskReinvest = 5
    ConstantInvest = 6
    Reinvest = 7


class TradeDirection(Enum):
    Long = 0
    Short = 1
    Both = 2
    BothInOneBot = 3
    Neither = 4
    Mode1 = 5
    Mode2 = 6
    Mode3 = 7


class TimeframeUnits(Enum):
    Sec = 0
    Min = 1
    Hour = 2
    Day = 3
    Week = 4


class PastFuture(Enum):
    Past = 0
    Future = 1


class PriceMode(Enum):
    Value = 0
    Previous = 1
    Delta = 2


class IdfPathIndices(Enum):
    IdfNdx = 0
    Pepper = 1
    PepperCommission = 2
    Raw = 3  # IC Market raw trading
    RawCommission = 4
    Dukas = 5
    DukasCommission = 6


class Platforms(Enum):
    Mt5Live = 0
    Mt5Backtest = 1
    MeFiles = 2
    cTrader = 3
    Csv = 4


class MovingAverageType(Enum):
    Simple = 0  # Match cTrader API (starts at 0)
    Exponential = 1
    TimeSeries = 2
    Triangular = 3
    Vidya = 4
    Weighted = 5
    WilderSmoothing = 6
    Hull = 7


class ChartIconType(Enum):
    #
    # Summary:
    #     The Up Arrow icon.
    UpArrow = 0
    #
    # Summary:
    #     The Down Arrow icon.
    DownArrow = 1
    #
    # Summary:
    #     The Circle icon.
    Circle = 2
    #
    # Summary:
    #     The Square icon.
    Square = 3
    #
    # Summary:
    #     The Diamond icon.
    Diamond = 4
    #
    # Summary:
    #     The Star icon.
    Star = 5
    #
    # Summary:
    #     The Up Triangle icon.
    UpTriangle = 6
    #
    # Summary:
    #     The Down Triangle icon.
    DownTriangle = 7


class RunMode(Enum):
    #
    # Summary:
    #     The cBot is running in real time.
    RealTime = 0
    #
    # Summary:
    #     The cBot is running in the silent backtesting mode.
    SilentBacktesting = 1
    #
    # Summary:
    #     The cBot is running in the visual backtesting mode.
    VisualBacktesting = 2
    #
    # Summary:
    #     The cBot is running in the Optimization mode.
    BruteForceOptimization = 3
    GeneticOptimization = 4
    WalkForwardOptimization = 5


class TradeType(Enum):
    #
    # Summary:
    #     Represents a buy order.
    Buy = 0
    #
    # Summary:
    #     Represents a Sell order.
    Sell = 1


class TotalMarginCalculationType(Enum):
    # Defines types of total margin requirements per Symbol.
    Sum = 0

    # Total margin requirements per Symbol are equal to Sum of all margin requirements of all Positions of that Symbol.
    Max = 1

    """
    Total margin requirements per Symbol are equal to Max margin requirements from
    all Long and all Short Positions of that Symbol.
    """
    Net = 2


class PendingOrderType(Enum):
    """
    Represents the type (Limit or stop) of pending order.
    """

    Limit = 0
    """
    A limit order is an order to buy or sell at a specific price or better.
    """

    Stop = 1
    """
    A stop order is an order to buy or sell once the price of the symbol reaches a specified price.
    """

    StopLimit = 2
    """
    A stop limit order is an order to buy or sell once the price of the symbol reaches specific price.
    Order has a parameter for maximum distance from that target price, where it can be executed.
    """


class StopTriggerMethod(Enum):
    """
    The trigger side for the stop Orders.
    """

    Trade = 0
    """
    trade method uses default trigger behavior for stop orders.
    buy order and stop Loss for Sell Position will be triggered when ask >= order price.
    Sell order and stop Loss for buy Position will be triggered when bid <= order price.
    """

    Opposite = 1
    """
    Opposite method uses opposite price for order triggering.
    buy order and stop Loss for Sell Position will be triggered when bid >= order price.
    Sell order and stop Loss for buy Position will be triggered when ask <= order price.
    """

    DoubleTrade = 2
    """
    Uses default prices for order triggering, but waits for
    additional confirmation - two consecutive prices should meet criteria to trigger order.
    buy order and stop Loss for Sell Position will be triggered when two consecutive ask prices >= order price.
    Sell order and stop Loss for buy Position will be triggered when two consecutive bid prices <= order price.
    """

    DoubleOpposite = 3
    """
    Uses opposite prices for order triggering, and waits for
    additional confirmation - two consecutive prices should meet criteria to trigger order.
    buy order and stop Loss for Sell Position will be triggered when two consecutive bid prices >= order price.
    Sell order and stop Loss for buy Position will be triggered when two consecutive ask prices <= order price.
    """


class ErrorCode(Enum):
    """
    Enumeration of standard error codes.

    Remarks:
        Error codes are readable descriptions of the responses returned by the server.
    """

    TechnicalError = 0
    """
    A generic technical error with a trade request.
    """

    BadVolume = 1
    """
    The volume value is not valid.
    """

    NoMoney = 2
    """
    There are not enough money in the Account to trade with.
    """

    MarketClosed = 3
    """
    The market is closed.
    """

    Disconnected = 4
    """
    The server is Disconnected.
    """

    EntityNotFound = 5
    """
    Position does not exist.
    """

    Timeout = 6
    """
    Operation timed out.
    """

    UnknownSymbol = 7
    """
    Unknown symbol.
    """

    InvalidStopLossTakeProfit = 8
    """
    The invalid stop Loss or Take Profit.
    """

    InvalidRequest = 9
    """
    The invalid request.
    """


class SymbolCommissionType(Enum):
    #
    # Summary:
    #     commission is in USD per millions USD volume.
    UsdPerMillionUsdVolume = 0
    #
    # Summary:
    #     commission is in USD per one symbol lot.
    UsdPerOneLot = 1
    #
    # Summary:
    #     commission is in Percentage of trading volume.
    PercentageOfTradingVolume = 2
    #
    # Summary:
    #     commission is in symbol quote Asset / currency per one lot.
    QuoteCurrencyPerOneLot = 3

    # Summary:
    # Defines symbol minimum commission types.


class SymbolMinCommissionType(Enum):
    #
    # Summary:
    #     Symbol minimum commission type is in symbol min_commission_asset.
    Asset = 0
    #
    # Summary:
    #     Symbol minimum commission type is in Symbol Quote Asset
    quote_asset = 1


class SymbolSwapCalculationType(Enum):
    """
    Defines the types of calculation for symbol SWAP Long/Short.
    """

    Pips = 0
    """
    Symbol SWAP Long/Short is in Pips.
    """
    Percentage = 1
    """
    Symbol SWAP Long/Short is in Percent (%).
    """


class SymbolTradingMode(Enum):
    """
    Defines symbol trading modes.
    """

    FullAccess = 0
    """
    Full access mode.
    """
    CloseOnly = 1
    """
    Close only mode.
    """
    DisabledWithPendingOrderExecution = 2
    """
    Trading is disabled but pending order execution is allowed mode.
    """
    FullyDisabled = 3
    """
    Trading is fully disabled mode.
    """


class SymbolMinDistanceType(Enum):
    """
    Defines symbol minimum distance types.
    """

    Pips = 0
    """
    Symbol minimum distances are in Pips.
    """
    Percentage = 1
    """
    Symbol minimum distances are in Percentage difference.
    """


class RoundingMode(Enum):
    """
    The rounding mode for normalizing trade volume.
    """

    ToNearest = 0
    """
    Round value to the nearest tradable volume.
    """
    Down = 1
    """
    Round value down to tradable volume.
    """
    Up = 2
    """
    Round value up to tradable volume.
    """


class ProportionalAmountType(Enum):
    """
    Defines types of amounts you can use for using symbol volume methods.
    """

    Balance = 0
    """
    Account Balance.
    """
    Equity = 1
    """
    Account Equity.
    """

    # end of file


# end of file
