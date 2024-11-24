from enum import Enum


class ChartIconType(Enum):
    #
    # Summary:
    #     The Up Arrow icon.
    up_arrow = (0,)
    #
    # Summary:
    #     The Down Arrow icon.
    down_arrow = (1,)
    #
    # Summary:
    #     The Circle icon.
    circle = (2,)
    #
    # Summary:
    #     The Square icon.
    square = (3,)
    #
    # Summary:
    #     The Diamond icon.
    diamond = (4,)
    #
    # Summary:
    #     The Star icon.
    star = (5,)
    #
    # Summary:
    #     The Up Triangle icon.
    up_triangle = (6,)
    #
    # Summary:
    #     The Down Triangle icon.
    down_triangle = 7


####################### API enums #######################
#
# Summary:
#     Defines if a cBot is running in real time, in the silent backtesting mode, in
#     the visual backtesting mode, or in the optimization mode.
class RunningMode(Enum):
    #
    # Summary:
    #     The cBot is running in real time.
    real_time = 0
    #
    # Summary:
    #     The cBot is running in the silent backtesting mode.
    silent_backtesting = 1
    #
    # Summary:
    #     The cBot is running in the visual backtesting mode.
    visual_backtesting = 2
    #
    # Summary:
    #     The cBot is running in the optimization mode.
    optimization = 3


#
# Summary:
#     The direction of a trade order.
#
# Remarks:
#     Indicates the trade direction, whether it is a buy or a Sell trade.
class TradeType(Enum):
    #
    # Summary:
    #     Represents a buy order.
    buy = 0
    #
    # Summary:
    #     Represents a Sell order.
    sell = 1


class AccountType(Enum):
    """
    Returns current Account type.
    """

    # Account type that allows hedged Positions
    hedged = 0

    # Account type that allows only single net Position per symbol
    netted = 1


class TotalMarginCalculationType(Enum):
    """
    Defines types of total margin requirements per Symbol.
    """

    sum = 0
    """
    Total margin requirements per Symbol are equal to Sum of all margin requirements
    of all Positions of that Symbol.
    """

    max = 1
    """
    Total margin requirements per Symbol are equal to Max margin requirements from
    all Long and all Short Positions of that Symbol.
    """

    net = 2
    """
    Total margin requirements per Symbol are equal to the difference between margin
    requirements of all Long and all Short Positions of that Symbol.
    """


class PendingOrderType(Enum):
    """
    Represents the type (Limit or Stop) of pending order.
    """

    limit = 0
    """
    A limit order is an order to buy or sell at a specific price or better.
    """

    stop = 1
    """
    A stop order is an order to buy or sell once the price of the symbol reaches a specified price.
    """

    stop_limit = 2
    """
    A stop limit order is an order to buy or sell once the price of the symbol reaches specific price.
    Order has a parameter for maximum distance from that target price, where it can be executed.
    """


class StopTriggerMethod(Enum):
    """
    The trigger side for the Stop Orders.
    """

    trade = 0
    """
    trade method uses default trigger behavior for Stop orders.
    buy order and Stop Loss for Sell Position will be triggered when ask >= order price.
    Sell order and Stop Loss for buy Position will be triggered when bid <= order price.
    """

    opposite = 1
    """
    Opposite method uses opposite price for order triggering.
    buy order and Stop Loss for Sell Position will be triggered when bid >= order price.
    Sell order and Stop Loss for buy Position will be triggered when ask <= order price.
    """

    double_trade = 2
    """
    Uses default prices for order triggering, but waits for
    additional confirmation - two consecutive prices should meet criteria to trigger order.
    buy order and Stop Loss for Sell Position will be triggered when two consecutive ask prices >= order price.
    Sell order and Stop Loss for buy Position will be triggered when two consecutive bid prices <= order price.
    """

    double_opposite = 3
    """
    Uses opposite prices for order triggering, and waits for
    additional confirmation - two consecutive prices should meet criteria to trigger order.
    buy order and Stop Loss for Sell Position will be triggered when two consecutive bid prices >= order price.
    Sell order and Stop Loss for buy Position will be triggered when two consecutive ask prices <= order price.
    """


class ErrorCode(Enum):
    """
    Enumeration of standard error codes.

    Remarks:
        Error codes are readable descriptions of the responses returned by the server.
    """

    technical_error = 0
    """
    A generic technical error with a trade request.
    """

    bad_volume = 1
    """
    The volume value is not valid.
    """

    no_money = 2
    """
    There are not enough money in the Account to trade with.
    """

    market_closed = 3
    """
    The market is closed.
    """

    disconnected = 4
    """
    The server is disconnected.
    """

    entity_not_found = 5
    """
    Position does not exist.
    """

    timeout = 6
    """
    Operation timed out.
    """

    unknown_symbol = 7
    """
    Unknown symbol.
    """

    invalid_stop_loss_take_profit = 8
    """
    The invalid Stop Loss or Take Profit.
    """

    invalid_request = 9
    """
    The invalid request.
    """


# Summary:
#     Defines symbol commission types.
class SymbolCommissionType(Enum):
    #
    # Summary:
    #     commission is in USD per millions USD volume.
    usd_per_million_usd_volume = 0
    #
    # Summary:
    #     commission is in USD per one symbol lot.
    usd_per_one_lot = 1
    #
    # Summary:
    #     commission is in Percentage of trading volume.
    percentage_of_trading_volume = 2
    #
    # Summary:
    #     commission is in symbol quote Asset / currency per one lot.
    quote_currency_per_one_lot = 3

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

    pips = 0
    """
    Symbol SWAP Long/Short is in pips.
    """
    percentage = 1
    """
    Symbol SWAP Long/Short is in Percent (%).
    """


class SymbolTradingMode(Enum):
    """
    Defines symbol trading modes.
    """

    full_access = 0
    """
    Full access mode.
    """
    close_only = 1
    """
    Close only mode.
    """
    disabled_with_PendingOrder_execution = 2
    """
    Trading is disabled but pending order execution is allowed mode.
    """
    fully_disabled = 3
    """
    Trading is fully disabled mode.
    """


class SymbolMinDistanceType(Enum):
    """
    Defines symbol minimum distance types.
    """

    pips = 0
    """
    Symbol minimum distances are in pips.
    """
    percentage = 1
    """
    Symbol minimum distances are in percentage difference.
    """


class RoundingMode(Enum):
    """
    The rounding mode for normalizing trade volume.
    """

    to_nearest = 0
    """
    Round value to the nearest tradable volume.
    """
    down = 1
    """
    Round value down to tradable volume.
    """
    up = 2
    """
    Round value up to tradable volume.
    """


class ProportionalAmountType(Enum):
    """
    Defines types of amounts you can use for using symbol volume methods.
    """

    balance = 0
    """
    Account Balance.
    """
    equity = 1
    """
    Account Equity.
    """

    # end of file
