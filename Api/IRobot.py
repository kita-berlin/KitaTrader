from abc import ABC, abstractmethod
from typing import TypeVar
from datetime import datetime, timedelta
from AlgoApiEnums import *
from AlgoApi import Account, Symbol, Position, Bars, LogParams, PyLogger, AlgoApi, BrokerProvider

# Define a TypeVar that can be float or int
T = TypeVar("T", float, int)


############### Interface needed for robots ####################
# The complete api which can be used by robots must be declarated here
# Varibales must be declared with their types
# Methods must be declared with their prototypes
class IRobot(ABC):

    # Trading api variable members
    # region
    algo_api: AlgoApi
    account: Account
    positions: list[Position]
    history: list[Position]
    initial_time: datetime
    initial_account_balance: float
    max_equity_drawdown_value: list[float]
    # the duration vars must be arrays because of by reference in max_duration() and min_duration()
    min_open_duration: list[timedelta] = [timedelta.max] * 1
    avg_open_duration_sum: list[timedelta] = [timedelta.min] * 1
    open_duration_count: list[int] = [0] * 1
    max_open_duration: list[timedelta] = [timedelta.min] * 1
    # endregion

    # Methods to be overridden in the robot
    # region
    @abstractmethod
    def on_start(self) -> None: ...

    @abstractmethod
    def on_tick(self, symbol: Symbol): ...

    @abstractmethod
    def on_stop(self) -> None: ...

    @abstractmethod
    def get_tick_fitness(self) -> float: ...

    # endregion

    # Trading API methods
    # region
    def init_symbol(
        self,
        symbol_name: str,
        asset_file: str,
        quote_provider: BrokerProvider,
        trade_provider: BrokerProvider,
    ) -> Symbol: ...
    def get_bars(self, timeframe_seconds: int, symbol_name: str) -> Bars: ...
    def close_trade(
        self,
        pos: Position,
        marginAfterOpen: float,
        min_open_duration: list[timedelta],
        avg_open_duration_sum: list[timedelta],
        open_duration_count: list[int],
        max_open_duration: list[timedelta],
        is_utc: bool = True,
    ) -> bool: ...
    def execute_market_order(  # type: ignore
        self, trade_type: TradeType, symbol_name: str, volume: float, label: str = ""
    ) -> Position: ...
    def close_position(self, pos: Position): ...

    # endregion

    # Long/Short and other arithmetic
    # region
    @abstractmethod
    def is_greater_or_equal_long(
        self, long_not_short: bool, val1: float, val2: float
    ) -> bool: ...

    @abstractmethod
    def is_less_or_equal_long(
        self, long_not_short: bool, val1: float, val2: float
    ) -> bool: ...

    @abstractmethod
    def is_greater_long(
        self, long_not_short: bool, val1: float, val2: float
    ) -> bool: ...

    @abstractmethod
    def is_less_long(self, long_not_short: bool, val1: float, val2: float) -> bool: ...

    @abstractmethod
    def is_crossing(
        self,
        long_not_short: bool,
        a_current: float,
        a_prev: float,
        b_current: float,
        b_prev: float,
    ) -> bool: ...

    @abstractmethod
    def add_long(self, long_not_short: bool, val1: float, val2: float) -> float: ...

    @abstractmethod
    def sub_long(self, long_not_short: bool, val1: float, val2: float) -> float: ...

    @abstractmethod
    def diff_long(self, long_not_short: bool, val1: float, val2: float) -> float: ...

    @abstractmethod
    def i_price(self, dPrice: float, tickSize: float) -> int: ...

    @abstractmethod
    def d_price(self, price: float, tickSize: float) -> float: ...

    @abstractmethod
    def max(self, ref_value: list[T], compare: T) -> bool: ...

    @abstractmethod
    def min(self, ref_value: list[T], compare: T) -> bool: ...

    @abstractmethod
    def sharpe_sortino(self, is_sortino: bool, vals: list[float]) -> float: ...

    @abstractmethod
    def standard_deviation(self, is_sortino: bool, vals: list[float]) -> float: ...

    @abstractmethod
    def is_new_bar_get(
        self, seconds: int, time: datetime, prevTime: datetime
    ) -> bool: ...

    # endregion

    # Logging
    # region
    @property
    def is_open(self) -> bool: ...

    def open_logfile(
        self,
        filename: str = "",
        mode: int = PyLogger.HEADER_AND_SEVERAL_LINES,
        header: str = "",
    ): ...

    def write_log_header(
        self,
        mode: int = PyLogger.HEADER_AND_SEVERAL_LINES,
        header: str = "",
    ): ...

    def log_add_text(self, s: str): ...

    def log_add_text_line(self, s: str): ...

    def log_closing_trade(self, lp: LogParams): ...

    def log_flush(self): ...

    def log_close(self, header_line: str = ""): ...

    # endregion

    # Price and lot/volume calculation
    # region
    @staticmethod
    def get_bid_ask_price(symbol: Symbol, bid_ask: BidAsk): ...

    @staticmethod
    def calc_profitmode_2lots(
        symbol: Symbol,
        profitMode: ProfitMode,
        value: float,
        tpPts: int,
        riskPoints: int,
        desired_money: list[float],
        lot_size: list[float],
    ): ...

    @staticmethod
    def calc_points_and_lot_2money(
        symbol: Symbol, points: int, lot: float
    ) -> float: ...

    @staticmethod
    def calc_points_and_volume_2money(
        symbol: Symbol, points: int, volume: float
    ) -> float: ...

    @staticmethod
    def calc_1point_and_1lot_2money(symbol: Symbol, reverse: bool = False): ...

    @staticmethod
    def calc_money_and_lot_2points(symbol: Symbol, money: float, lot: float): ...

    @staticmethod
    def calc_money_and_volume_2points(symbol: Symbol, money: float, volume: float): ...

    @staticmethod
    def calc_money_and_points_2lots(
        symbol: Symbol, money: float, points: int, xProLot: float
    ): ...

    # endregion


# end of file
