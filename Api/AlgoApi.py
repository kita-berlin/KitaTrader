import os
import math
import importlib.util
import importlib
import numpy as np
import csv
import traceback
import locale
from abc import ABC, abstractmethod
from numpy.typing import NDArray
from typing import TypeVar, Iterable, Iterator
from datetime import datetime, timedelta
from AlgoApiEnums import *
from CoFu import *


# Define a TypeVar that can be float or int
T = TypeVar("T", float, int)


# Due to circular import problmes with separated classe, we define them here
############# Some classes needed for AlgoApi ########################
class TradeResult:
    def __init__(self, is_successful: bool = True, error: str = None):  # type: ignore
        self.is_successful = is_successful
        self.error = error


class Bar:
    def __init__(
        self,
        open_time: datetime,
        open: float,
        high: float,
        low: float,
        close: float,
        tick_volume: int,
        open_ask: float,
    ):
        self.open_time = open_time
        self.open_price = open
        self.high_price = high
        self.low_price = low
        self.close_price = close
        self.tick_volume = tick_volume
        self.open_ask = open_ask


class QuoteBar:
    time: datetime = datetime.min
    milli_seconds: int = 0
    open: float = 0
    high: float = 0
    low: float = 0
    close: float = 0
    volume: int = 0
    open_ask: float = 0


class PyLogger:
    HEADER_AND_SEVERAL_LINES: int = 0
    NO_HEADER: int = 1
    ONE_LINE: int = 2
    SELF_MADE: int = 4
    mode: int

    def __init__(self):
        self.log_stream_writer = None
        self.mode: int = self.HEADER_AND_SEVERAL_LINES
        self.write_header = None

    @property
    def is_open(self):
        return self.log_stream_writer is not None

    def log_open(self, pathName: str, filename: str, append: bool, mode: int):
        self.mode = mode
        dir_path = os.path.join(os.path.dirname(pathName), os.path.dirname(filename))
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        new_file = self.make_unique_logfile_name(
            os.path.join(dir_path, os.path.basename(filename))
        )
        ret_val = os.path.exists(new_file)
        try:
            self.log_stream_writer = open(new_file, "a" if append else "w")
        except Exception:
            pass
        return ret_val

    def make_log_path(self):
        # terminal_common_data_path = os.path.join(os.environ.get("CALGO_SOURCES"), "..", "LogFiles")
        return os.path.join("Files", "Algo.csv")

    def add_text(self, text: str):
        if not self.is_open:
            return
        self.log_stream_writer.write(text)  # type: ignore

    def flush(self):
        if not self.is_open:
            return
        self.log_stream_writer.flush()  # type: ignore

    def close(self, header_line: str = ""):
        if not self.is_open:
            return
        # to_do: Insert headerline at the beginning of the file
        self.log_stream_writer.close()  # type: ignore

    def make_unique_logfile_name(self, path_name: str) -> str:
        """
        while os.path.exists(path_name):
            fn_ex = path_name.split('.')
            split_ex_size = len(fn_ex)
            if split_ex_size < 2:
                return ""

            name = '_'.join(fn_ex[:-1])
            ext = fn_ex[-1]

            fn_num = name.split('_')
            path_name = f"{fn_num[0]}_{int(fn_num[1]) + 1}.{ext}" if len(fn_num) > 1 else f"{name}_1.{ext}"
        """
        return path_name


class PendingOrder(ABC):
    """
    Provides access to properties of pending orders
    """

    @property
    @abstractmethod
    def symbol_code(self) -> str:
        """
        symbol code of the order
        """
        return ""

    #     @property
    #     @abstractmethod
    #     def trade_type(self) -> trade_type:
    #         """
    #         Specifies whether this order is to buy or sell.
    #         """
    #         pass

    #     @property
    #     @abstractmethod
    #     def volume(self) -> int:
    #         """
    #         Volume of this order.
    #         """
    #         pass

    #     @property
    #     @abstractmethod
    #     def initial_volume(self) -> float:
    #         """
    #         Volume of this order.
    #         """
    #         pass

    @property
    @abstractmethod
    def id(self) -> int:
        """
        Unique order Id.
        """
        pass

    # Pending order out commentet
    # region
    #     @property
    #     @abstractmethod
    #     def order_type(self) -> PendingOrder_type:
    #         """
    #         Specifies whether this order is stop or Limit.
    #         """
    #         pass

    #     @property
    #     @abstractmethod
    #     def target_price(self) -> float:
    #         """
    #         The order target price.
    #         """
    #         pass

    #     @property
    #     @abstractmethod
    #     def expiration_time(self) -> datetime:
    #         """
    #         The order Expiration time
    #         """
    #         return datetime.min

    #     @property
    #     @abstractmethod
    #     def stop_loss(self) -> float:
    #         """
    #         The order stop loss in price
    #         """
    #         pass

    #     @property
    #     @abstractmethod
    #     def stop_loss_pips(self) -> float:
    #         """
    #         The order stop loss in Pips
    #         """
    #         pass

    #     @property
    #     @abstractmethod
    #     def take_profit_percent(self) -> float:
    #         """
    #         The order take profit in price
    #         """

    #     @property
    #     @abstractmethod
    #     def take_profit_pips(self) -> float:
    #         """
    #         The order take profit in Pips
    #         """

    #     @property
    #     @abstractmethod
    #     def label(self) -> str:
    #         """
    #         User assigned identifier for the order.
    #         """
    #         return ""

    #     @property
    #     @abstractmethod
    #     def comment(self) -> str:
    #         """
    #         User assigned Order Comment
    #         """
    #         return ""

    #     @property
    #     @abstractmethod
    #     def quantity(self) -> float:
    #         """
    #         Quantity (lots) of this order
    #         """
    #         pass

    #     @property
    #     @abstractmethod
    #     def has_trailing_stop(self) -> bool:
    #         """
    #         When has_trailing_stop set to true, server updates stop Loss every time Position moves in your favor.
    #         """
    #         pass

    #     @property
    #     @abstractmethod
    #     def stop_loss_trigger_method(self) -> stop_trigger_method:
    #         """
    #         Trigger method for Position's stop_loss
    #         """
    #         pass

    #     @property
    #     @abstractmethod
    #     def stop_order_trigger_method(self) -> stop_trigger_method:
    #         """
    #         Determines how pending order will be triggered in case it's a stop_order
    #         """
    #         pass

    #     @property
    #     @abstractmethod
    #     def stop_limit_range_pips(self) -> float:
    #         """
    #         Maximum limit from order target price, where order can be executed.
    #         """
    #         pass

    #     # Obsolete. Use symbol.name instead
    #     # @property
    #     # @abstractmethod
    #     # def symbol_name(self) -> str:
    #     #     """
    #     #     Gets the symbol name.
    #     #     """
    #     #     pass

    #     @abstractmethod
    #     def modify_stop_loss_pips(self, stopLossPips: float]) -> trade_result:
    #         """
    #         Shortcut for Robot.modify_PendingOrder method to change stop Loss
    #         """
    #         pass

    #     @abstractmethod
    #     def modify_take_profit_pips(self, takeProfitPips: float]) -> trade_result:
    #         """
    #         Shortcut for Robot.modify_PendingOrder method to change Take Profit
    #         """
    #         pass

    #     @abstractmethod
    #     def modify_stop_limit_range(self, stopLimitRangePips: float) -> trade_result:
    #         """
    #         Shortcut for Robot.modify_PendingOrder method to change stop Limit Range
    #         """
    #         pass

    #     @abstractmethod
    #     def modify_expiration_time(self, expirationTime: datetime]) -> trade_result:
    #         """
    #         Shortcut for Robot.modify_PendingOrder method to change Expiration Time
    #         """
    #         pass

    #     @abstractmethod
    #     def modify_volume(self, volume: float) -> trade_result:
    #         """
    #         Shortcut for Robot.modify_PendingOrder method to change initial_volume
    #         """
    #         pass

    #     @abstractmethod
    #     def modify_target_price(self, targetPrice: float) -> trade_result:
    #         """
    #         Shortcut for Robot.modify_PendingOrder method to change Target Price
    #         """
    #         pass

    #     @abstractmethod
    #     def cancel(self) -> trade_result:
    #         """
    #         Shortcut for Robot.cancel_PendingOrder method
    #         """
    #         pass
    # endregion


class TradingSession:
    @property
    def start_time(self) -> datetime:
        return datetime.min

    @property
    def end_time(self) -> datetime:
        return datetime.min


class MarketHours:
    @property
    def sessions(self) -> list[TradingSession]:
        # create list
        return list()

    # def is_opened(self) -> bool:
    #     pass

    # def is_opened(self, datetime: datetime) -> bool:
    #     pass

    def is_opened(self, datetime: datetime = None) -> bool:  # type:ignore
        if datetime is not None:  # type:ignore
            # Logic for checking if trading session is active at a specific datetime
            return True

        else:
            # Logic for checking if trading session is active at current time
            return True

    def time_till_close(self) -> timedelta:
        return timedelta.min

    def time_till_open(self) -> timedelta:
        return timedelta.min


class LogParams:
    def __init__(self):
        self.symbol: Symbol
        self.lots: float
        self.volume_in_units: float
        self.balance: float
        self.minlots: float
        self.trade_margin: float
        self.account_margin: float
        self.trade_type: TradeType
        self.entry_time: datetime
        self.closing_time: datetime
        self.entry_price: float
        self.closing_price: float
        self.comment: str
        self.commissions: float
        self.swap: float
        self.net_profit: float
        self.max_equity_drawdown: float
        self.max_trade_equity_drawdown_value: float


class LeverageTier:
    """leverage Steps"""

    @property
    def volume(self) -> float:
        return 0

    @property
    def leverage(self) -> float:
        return 0


class Asset(ABC):
    """
    The Asset represents a currency.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        The Asset Name
        """
        return ""

    @property
    @abstractmethod
    def digits(self) -> int:
        """
        Number of Asset digits
        """
        return 0

    @abstractmethod
    def convert(self, to: float, value: float):
        """
        Converts value to another Asset.

        gui_parameters:
          to:
            Target Asset

          value:
            The value you want to convert from current Asset

        Returns:
            Value in to / target Asset
        """
        if isinstance(to, Asset):
            # Handle conversion to Asset
            return None

        elif isinstance(to, str):
            # Handle conversion to string
            return None

        else:
            raise ValueError("Unsupported conversion target")


class Account:
    balance: float
    equity: float
    margin: float
    free_margin: float
    margin_level: float
    unrealized_net_profit: float
    leverage: float
    stop_out_level: float
    asset: str
    # total_margin_calculation_type:MarginMode
    # credit = account_info.credit
    # user_nick_name = account_info.name

    def __init__(self):
        pass


class ConcreteAsset(Asset):
    def __init__(self, name: str, digits: int):
        self._name = name
        self._digits = digits

    @property
    def name(self) -> str:
        return self.name

    @property
    def digits(self) -> int:
        return self._digits

    # def convert(self, to: Asset, value: float) -> None:
    # Implement conversion logic here


class IIndicator(ABC):
    _isLastBar: bool = False
    _index: int = 0

    @property
    def is_last_bar(self) -> bool:
        """Returns true if Calculate is invoked for the last bar."""
        return self._isLastBar

    @is_last_bar.setter
    def is_last_bar(self, value: bool):
        self._is_last_bar = value

    @abstractmethod
    def calculate(self, index: int):
        """Calculate the value(s) of the indicator for the given index."""
        pass

    @abstractmethod
    def initialize(self):
        """Custom initialization for the Indicator. This method is invoked when an indicator is launched."""
        pass

    def on_destroy(self):
        """Called when Indicator is destroyed."""
        pass

    def __str__(self) -> str:
        """The name of the indicator derived class."""
        return self.__class__.__name__


class TimeSeries(Iterable[datetime]):
    def __init__(self):
        self.data = np.array([], dtype="datetime64[D]")

    def __getitem__(self, index: int) -> datetime:
        return self.data[index].astype(datetime)  # Convert numpy.datetime64 to datetime

    def __iter__(self) -> Iterator[datetime]:
        return (item.astype(datetime) for item in self.data)  # Generator for iteration

    @property
    def last_value(self) -> datetime:  # Gets the last value of this time series.
        return self.data[-1]

    @property
    def count(self) -> int:  # Gets the number of elements contained in the series.
        return len(self.data)

    def last(
        self, index: int
    ) -> datetime:  # Access a value in the data series certain number of bars ago.
        return self.data[self.count - index - 1]

    def get_index_by_exact_time(self, dateTime: datetime) -> int:
        """
        Find the index in the different time frame series.

        gui_parameters:
          dateTime:
            The open time of the bar at this index.
        """
        raise NotImplementedError

    def get_index_by_time(self, dateTime: datetime) -> int:
        """
        Find the index in the different time frame series.

        gui_parameters:
          dateTime:
            The open time of the bar at this index.
        """
        raise NotImplementedError


class DataSeries(Iterable[float]):
    def __init__(self):
        self.indicator_list: list[IIndicator] = []
        self.data: NDArray[np.float64] = np.array([], dtype=np.float64)

    def __getitem__(self, index: int) -> float:
        if index < 0:
            index += len(self.data)
        if index >= len(self.data) or index < 0:
            raise IndexError("Index out of range")
        return self.data[index]

    def __setitem__(self, index: int, value: float):
        """Set the value at a specific index in the data series."""
        if index < 0:
            index += len(self.data)
        if index >= len(self.data) or index < 0:
            raise IndexError("Index out of range")
        self.data[index] = value

    def __iter__(self) -> Iterator[float]:
        return iter(self.data)

    @property
    def last_value(self) -> float:
        """Gets the last value of this DataSeries."""
        if self.count == 0:
            raise IndexError("DataSeries is empty, no last value available.")
        return self.data[-1]

    @property
    def count(self) -> int:
        """Gets the number of elements contained in the series."""
        return len(self.data)

    def last(self, index: int) -> float:
        """Access a value in the dataseries certain bars ago."""
        if index < 0 or index >= self.count:
            raise IndexError("Index out of range for last()")
        return self.data[self.count - index - 1]

    def append(self, value: float):
        """Append a new value to the DataSeries."""
        self.data = np.append(self.data, value)

    # def update_indicators(self, index: int, isNewBar: bool):
    #     """Update indicators based on the current index."""
    #     for indi in self.indicator_list:
    #         while indi._index <= index:
    #             indi.is_last_bar = indi._index == index
    #             indi.calculate(indi._index)
    #             if indi.is_last_bar:
    #                 break
    #             else:
    #                 indi._index += 1


class StandardDeviation(IIndicator):
    result: DataSeries = DataSeries()

    def __init__(
        self,
        source: DataSeries,
        periods: int = 14,
        ma_type: MovingAverageType = MovingAverageType.Simple,
    ):
        self.source: DataSeries = source
        self.periods: int = periods
        self.ma_type: MovingAverageType = ma_type
        self.initialize()
        pass

    def initialize(self):
        self._movingAverage: MovingAverage = SimpleMovingAverage(
            self.source, self.periods
        )

    def calculate(self, index: int) -> None:
        num1: float = 0.0
        num2: float = self._movingAverage.result[index]
        num3: int = 0
        while num3 < self.periods:
            if index - num3 < 0:
                break
            num1 += (self.source[index - num3] - num2) ** 2
            num3 += 1

        self.result[index] = np.sqrt(num1 / self.periods)


class BollingerBands(IIndicator):
    Main: DataSeries = DataSeries()
    Top: DataSeries = DataSeries()
    Bottom: DataSeries = DataSeries()

    def __init__(
        self,
        source: DataSeries,
        periods: int = 20,
        standard_deviations: float = 2.0,
        ma_type: MovingAverageType = MovingAverageType.Simple,
        shift: int = 0,
    ):
        self.source: DataSeries = source
        self.periods: int = periods
        self.standard_deviations: float = standard_deviations
        self.ma_type: MovingAverageType = ma_type
        self.shift: int = shift

        self.MovingAverage = None
        self.StandardDeviation = None

        self.initialize()
        pass

    def initialize(self):
        self.MovingAverage = SimpleMovingAverage(self.source, self.periods)
        self.StandardDeviation = StandardDeviation(self.source, self.periods)

    def calculate(self, index: int) -> None:
        for index in range(self.source.count):
            index1 = index + self.shift
            if index1 >= self.source.count or index1 < 0:
                continue

            num = self.StandardDeviation.result.data[index] * self.standard_deviations  # type: ignore
            self.Main[index1] = self.MovingAverage.result.data[index]  # type: ignore
            self.Bottom[index1] = self.MovingAverage.result.data[index] - num  # type: ignore
            self.Top[index1] = self.MovingAverage.result.data[index] + num  # type: ignore


class MovingAverage(IIndicator, ABC):
    result: DataSeries = DataSeries()
    pass


class SimpleMovingAverage(MovingAverage, IIndicator):
    def __init__(self, source: DataSeries, periods: int = 14, shift: int = 0):
        self.source: DataSeries = source
        self.periods: int = periods
        self.shift: int = shift

        self.initialize()
        pass

    def initialize(self) -> None:
        pass

    def calculate(self, index: int) -> None:
        index1 = index + self.shift
        num = 0.0
        index2 = index - self.periods + 1
        while index2 <= index:
            num += self.source[index2]
            index2 += 1
        self.result[index1] = num / self.periods


class Indicators:
    indicator_list = []

    def __init__(self):
        pass

    def moving_average(
        self,
        source: DataSeries,
        periods: int = 14,
        ma_type: MovingAverageType = MovingAverageType.Simple,
    ) -> MovingAverage:
        if MovingAverageType.Simple == ma_type:
            indicator = SimpleMovingAverage(source, periods)
            # if MovingAverageType...

            source.indicator_list.append(indicator)
            return indicator
        return None  # type: ignore
        pass

    def standard_deviation(
        self,
        source: DataSeries,
        periods: int = 14,
        ma_type: MovingAverageType = MovingAverageType.Simple,
    ) -> StandardDeviation:
        indicator = StandardDeviation(source, periods, ma_type)
        source.indicator_list.append(indicator)
        return indicator
        pass

    def bollinger_bands(
        self,
        source: DataSeries,
        periods: int = 20,
        standard_deviations: float = 2.0,
        ma_type: MovingAverageType = MovingAverageType.Simple,
        shift: int = 0,
    ) -> BollingerBands:
        indicator = BollingerBands(source, periods, standard_deviations, ma_type, shift)
        source.indicator_list.append(indicator)
        return indicator

    # Hide
    # region
    # def exponential_moving_average(self, source: DataSeries, periods: int):
    #     # Exponential Moving Average indicator instance
    #     pass

    # def weighted_moving_average(self, source: DataSeries, periods: int):
    #     # Weighted Moving Average indicator instance
    #     pass

    # def SimpleMovingAverage(self, source: DataSeries, periods: int):
    #     # Simple Moving Average indicator instance
    #     pass

    # def triangular_moving_average(self, source: DataSeries, periods: int):
    #     # Triangular Moving Average indicator instance
    #     pass

    # def high_minus_low(self, bars=None):
    #     # High Minus Low indicator instance with bars
    #     if None == bars:
    #         bars = self.bars

    #     pass

    # def true_range(self, bars):
    #     # True Range indicator instance with bars
    #     if None == bars:
    #         bars = self.bars

    #     pass

    # def welles_wilder_smoothing(self, source: DataSeries, periods: int):
    #     # Welles Wilder Smoothing indicator instance
    #     pass

    # def hull_moving_average(self, source: DataSeries, periods: int):
    #     # Hull Moving Average indicator instance
    #     pass

    # def swing_index(self, limitMoveValue, bars: Bars = None):
    #     # Swing Index indicator instance with bars
    #     pass

    # def accumulative_swing_index(self, limitMoveValue, bars: Bars = None):
    #     # Accumulative Swing Index indicator instance with bars
    #     pass

    # def aroon(self, bars: Bars, periods: int):
    #     # Aroon indicator instance with bars
    #     pass

    # def relative_strength_index(self, source: DataSeries, periods: int):
    #     # Relative Strength Index indicator instance
    #     pass

    # def time_series_moving_average(self, source: DataSeries, periods: int):
    #     # Time Series Moving Average indicator instance
    #     pass

    # def linear_regression_forecast(self, source: DataSeries, periods: int):
    #     # Linear Regression Forecast indicator instance
    #     pass

    # def linear_regression_r_squared(self, source: DataSeries, periods: int):
    #     # Linear Regression R-Squared indicator instance
    #     pass

    # def price_roc(self, source: DataSeries, periods: int):
    #     # Price Rate of Change indicator instance
    #     pass

    # def vidya(self, source: DataSeries, periods: int, r2Scale):
    #     # Vidya indicator instance
    #     pass

    # def ultimate_oscillator(self, bars: Bars, cycle1: int, cycle2: int, cycle3: int):
    #     # Ultimate Oscillator indicator instance with bars
    #     pass

    # def directional_movement_system(self, bars: Bars, periods: int):
    #     # Directional Movement System indicator instance with bars
    #     pass

    # def parabolic_sar(self, bars: Bars, minAf: float, maxAf: float):
    #     # Parabolic SAR indicator instance with bars
    #     pass

    # def stochastic_oscillator(self, bars: Bars, kPeriods, kSlowing, dPeriods, ma_type):
    #     # Stochastic Oscillator indicator instance with bars
    #     pass

    # def momentum_oscillator(self, source: DataSeries, periods: int):
    #     # Momentum Oscillator indicator instance
    #     pass

    # def median_price(self, bars):
    #     # Median Price indicator instance with bars
    #     if None == bars:
    #         bars = self.bars

    #     pass

    # def williams_accumulation_distribution(self, bars):
    #     # Williams Accumulation Distribution indicator instance with bars
    #     if None == bars:
    #         bars = self.bars

    #     pass

    # def fractal_chaos_bands(self, bars):
    #     # Fractal Chaos Bands indicator instance with bars
    #     if None == bars:
    #         bars = self.bars

    #     pass

    # def typical_price(self, bars):
    #     # Typical Price indicator instance with bars
    #     if None == bars:
    #         bars = self.bars

    #     pass

    # def commodity_channel_index(self, bars: Bars, periods: int):
    #     # Commodity Channel Index indicator instance with bars
    #     pass

    # def historical_volatility(self, source: DataSeries, periods: int, barHistory):
    #     # Historical Volatility indicator instance
    #     pass

    # def mass_index(self, bars: Bars, periods: int):
    #     # Mass Index indicator instance with bars
    #     pass

    # def chaikin_volatility(self, bars: Bars, periods: int, rateOfChange, ma_type):
    #     # Chaikin Volatility indicator instance with bars
    #     pass

    # def detrended_price_oscillator(self, source: DataSeries, periods: int, ma_type):
    #     # Detrended Price Oscillator indicator instance
    #     pass

    # def linear_regression_intercept(self, source: DataSeries, periods: int):
    #     # Linear Regression Intercept indicator instance
    #     pass

    # def linear_regression_slope(self, source: DataSeries, periods: int):
    #     # Linear Regression Slope indicator instance
    #     pass

    # def macd_histogram(self, source: DataSeries, longCycle, shortCycle, signalPeriods):
    #     # MACD Histogram indicator instance with DataSeries source
    #     pass

    # def macd_cross_over(self, source: DataSeries, longCycle, shortCycle, signalPeriods):
    #     # MACD cross_over indicator instance with DataSeries source
    #     pass

    # def price_oscillator(self, source: DataSeries, longCycle, shortCycle, ma_type):
    #     # Price Oscillator indicator instance
    #     pass

    # def rainbow_oscillator(self, source: DataSeries, levels, ma_type):
    #     # Rainbow Oscillator indicator instance
    #     pass

    # def vertical_horizontal_filter(self, source: DataSeries, periods: int):
    #     # Vertical Horizontal Filter indicator instance
    #     pass

    # def williams_pct_r(self, bars: Bars, periods: int):
    #     # Williams Percent R indicator instance with bars
    #     pass

    # def trix(self, source: DataSeries, periods: int):
    #     # Trix indicator instance
    #     pass

    # def weighted_close(self, bars):
    #     # Weighted Close indicator instance with bars
    #     if None == bars:
    #         bars = self.bars

    #     pass

    # def chaikin_money_flow(self, bars: Bars, periods: int):
    #     # Chaikin Money Flow indicator instance with bars
    #     pass

    # def ease_of_movement(self, periods: int, ma_type):
    #     # Ease Of Movement indicator instance
    #     bars = self.bars

    #     pass

    # def money_flow_index(self, bars: Bars, periods: int):
    #     # Money Flow Index indicator instance with bars
    #     pass

    # def negative_volume_index(self, source):
    #     # Negative Volume Index indicator instance
    #     pass

    # def on_balance_volume(self, source):
    #     # On Balance Volume indicator instance
    #     pass

    # def positive_volume_index(self, source):
    #     # Positive Volume Index indicator instance
    #     pass

    # def price_volume_trend(self, source):
    #     # Price Volume Trend indicator instance
    #     pass

    # def trade_volume_index(self, source):
    #     # trade Volume Index indicator instance
    #     pass

    # def volume_oscillator(self, bars: Bars, shortTerm, longTerm):
    #     # Volume Oscillator indicator instance with bars
    #     pass

    # def volume_roc(self, bars: Bars, periods: int):
    #     # Volume Rate of Change indicator instance with bars
    #     pass

    # def average_true_range(self, bars: Bars, periods: int, ma_type):
    #     # Average True Range indicator instance with bars
    #     pass

    # def donchian_channel(self, periods: int):
    #     # Donchian Channel indicator instance
    #     pass

    # # endregion


class Bars:
    # bars are not indexed; only time and data series are indexed
    # No bars.Last().open_time; Use bars.open_times.Last() instead
    # So no: def __getitem__(self, index: int) -> Bar: # Returns a bar based on its index#
    # and no: @property
    # def last_bar(self) -> Bar: # Gets the last bar in the chart.#

    # Members
    # region
    @property
    def count(self) -> int:  # Gets the number of bars.#
        return len(self.open_times.data)

    default_timeframe_seconds: int  # Get the timeframe in seconds.#
    symbol_name: str  # Gets the symbol name.#
    open_prices: DataSeries  # Gets the Open price bars data.#
    high_prices: DataSeries  # Gets the High price bars data.#
    low_prices: DataSeries  # Gets the Low price bars data.#
    close_prices: DataSeries  # Gets the Close price bars data.#
    tick_volumes: DataSeries  # Gets the tick volumes data.#
    open_asks: DataSeries  # The ask value at open time (open_prices are bids)
    open_times: TimeSeries  # Gets the open bar time data.#
    is_new_bar: bool = False
    chart_time_array = []
    # endregion

    # forward declarations
    def is_new_bar_get(
        self, seconds: int, time: datetime, prevTime: datetime
    ) -> bool: ...

    def __init__(self, timeframe_seconds: int, symbol_name: str):
        self.default_timeframe_seconds = timeframe_seconds
        self.symbol_name = symbol_name

        # Create initial OHLC data for drawing
        self.open_times = TimeSeries()
        self.open_prices = DataSeries()
        self.high_prices = DataSeries()
        self.low_prices = DataSeries()
        self.close_prices = DataSeries()
        self.tick_volumes = DataSeries()
        self.open_asks = DataSeries()
        self.line_colors = np.array([])

    pass

    ######################################
    def update_bar(self, quote: QuoteBar) -> None:
        self.is_new_bar = False

        # do we have to build a new bar ?
        # epoc_dt = quote.time.timestamp() // 60
        # tf_minutes = self.default_timeframe_seconds // 60
        # tf_modulo = epoc_dt % tf_minutes
        if 0 == self.open_times.count or self.is_new_bar_get(
            self.default_timeframe_seconds, quote.time, self.open_times.data[-1]
        ):
            self.open_times.data = np.append(
                self.open_times.data, np.datetime64(quote.time, "D")
            )
            self.open_prices.data = np.append(self.open_prices.data, quote.open)
            self.high_prices.data = np.append(self.high_prices.data, quote.open)
            self.low_prices.data = np.append(self.low_prices.data, quote.open)
            self.close_prices.data = np.append(self.close_prices.data, quote.open)
            self.tick_volumes.data = np.append(self.tick_volumes.data, 0)
            self.open_asks.data = np.append(self.open_asks.data, quote.open_ask)
            self.line_colors = np.append(self.line_colors, "green")
            self.is_new_bar = True
        else:
            self.high_prices.data[-1] = max(self.high_prices.data[-1], quote.high)
            self.low_prices.data[-1] = min(self.low_prices.data[-1], quote.low)
            self.close_prices.data[-1] = quote.close
            self.tick_volumes.data[-1] += (
                1 if 0 == self.tick_volumes.data[-1] else self.tick_volumes.data[-1]
            )
            self.line_colors[-1] = (
                "green"
                if self.close_prices.data[-1] > self.open_prices.data[-1]
                else "red"
            )

        # self.open_prices.update_indicators(self.open_times.count - 1, self.is_new_bar)
        # self.high_prices.update_indicators(self.open_times.count - 1, self.is_new_bar)
        # self.low_prices.update_indicators(self.open_times.count - 1, self.is_new_bar)
        # self.close_prices.update_indicators(self.open_times.count - 1, self.is_new_bar)
        # self.tick_volumes.update_indicators(self.open_times.count - 1, self.is_new_bar)
        # self.open_asks.update_indicators(self.open_times.count - 1, self.is_new_bar)

    pass
    """
    @property
    def median_prices(self) -> DataSeries:
        # Gets the Median prices data (High + Low) / 2.#
        ...

    @property
    def typical_prices(self) -> DataSeries:
        # Gets the Typical prices data (High + Low + Close) / 2.#
        ...

    @property
    def weighted_prices(self) -> DataSeries:
        # Gets the Weighted prices data (High + Low + 2 * Close) / 4.#
        ...

    def load_more_history(self) -> int:
        # Loads more historical bars. Method returns the number of loaded bars that were added to the beginning of the collection.#
        ...

    def load_more_history_async(self) -> None:
        # Loads more historical bars asynchronously.#
        ...

    def load_more_history_async_callback(self, callback: Callable[[bars_history_loaded_event_args], None]) -> None:
        #Loads more historical bars asynchronously with a callback.#
        ...

    # Events
    def history_loaded_event(self, callback: Callable[[bars_history_loaded_event_args], None]) -> None:
        #Occurs when more history is loaded due to chart scroll on the left or due to API call.#
        ...

    def reloaded_event(self, callback: Callable[[bars_history_loaded_event_args], None]) -> None:
        #Occurs when bars are refreshed due to reconnect.#
        ...

    def tick_event(self, callback: Callable[[bars_tick_event_args], None]) -> None:
        #Occurs when a new tick arrives.#
        ...

    def bar_opened_event(self, callback: Callable[[bar_opened_event_args], None]) -> None:
        #Occurs when the last bar is closed and a new bar is opened.#
        ...

    def bar_closed_event(self, callback: Callable[[bar_closed_event_args], None]) -> None:
        #Occurs when a new bar is opened; the event is called for the previous (closed) bar.#
        ...
    """


class MarketValues:
    def __init__(self):
        self.symbol_name = ""
        self.swap_long = 0.0
        self.swap_short = 0.0
        self.point_size = 0.0
        self.avg_spread = 0.0
        self.digits = 0
        self.point_value = 0.0
        self.margin_required = 0.0
        self.symbol_tz_id = ""
        self.market_open_time = timedelta()
        self.market_close_time = timedelta()
        self.min_volume = 0.0
        self.max_volume = 0.0
        self.lot_size = 0.0
        self.commission = 0.0
        self.broker_symbol = ""
        self.symbol_leverage = 0.0
        self.symbol_currency_base = ""
        self.symbol_currency_quote = ""


class BrokerProvider(ABC):
    symbol_name: str
    account: Account
    market_values: MarketValues

    def __init__(self, parameter: str, data_rate: int, account: Account):
        self.parameter = parameter
        self.data_rate = data_rate
        self.account = account
        pass

    @abstractmethod
    def initialize(self, symbol_name: str): ...

    @abstractmethod
    def get_quote_bar_at_date(self, dt: datetime) -> tuple[str, QuoteBar]: ...

    @abstractmethod
    def get_first_quote_bar(self) -> tuple[str, QuoteBar]: ...

    @abstractmethod
    def get_next_quote_bar(self) -> tuple[str, QuoteBar]: ...

    @abstractmethod
    def update_account(self): ...


class SymbolInfo:
    # Members
    # region
    name: str = ""
    bars_list: list[Bars] = []
    time: datetime = datetime.min
    bid: float = 0
    ask: float = 0
    broker_symbol_name: str = ""
    min_volume: float = 0.0
    max_volume: float = 0.0
    lot_size: float = 0.0
    leverage: float = 0.0
    is_trading_allowed: bool = False
    # endregion

    def __init__(
        self,
        symbol_name: str,
        assets_file_name: str,
        quote_provider: BrokerProvider,
        trade_provider: BrokerProvider,
    ):
        self.name = symbol_name
        self.quote_provider = quote_provider
        self.trade_provider = trade_provider

        assets_path = os.path.join("Files", assets_file_name)
        self.market_values = self.quote_provider.market_values = (
            self.trade_provider.market_values
        ) = MarketValues()
        error = self.init_market_info(assets_path, symbol_name, self.market_values)
        if "" != error:
            print(error)
            exit()

        self.point_size = self.market_values.point_size
        self.min_volume = self.market_values.min_volume
        self.max_volume = self.market_values.max_volume
        self.lot_step = self.min_volume
        self.leverage = self.market_values.symbol_leverage
        self.lot_size = self.market_values.lot_size
        self.tick_value = self.market_values.point_value
        self.commission = self.market_values.commission
        self.swap_long = self.market_values.swap_long
        self.swap_short = self.market_values.swap_short
        self.swap3_days_rollover = 3
        self.base_asset = self.market_values.symbol_currency_base
        self.QuoteAsset = self.market_values.symbol_currency_quote
        self.swap_calculation_type: SymbolSwapCalculationType = (
            SymbolSwapCalculationType.Pips
        )
        self.is_trading_enabled = True
        self.trading_mode = SymbolTradingMode.FullAccess

        self.quote_provider.market_values = self.trade_provider.market_values = (
            self.market_values
        )

    @property
    def point_size(self) -> float:
        return self._tick_size

    @point_size.setter
    def point_size(self, value: float):
        self._tick_size: float = value
        self.digits = int(0.5 + math.log10(1 / value))

    @property
    def tick_value(self) -> float:
        return self._tick_value

    @tick_value.setter
    def tick_value(self, value: float):
        self._tick_value: float = value

    @property
    def pip_value(self) -> float:
        return self._tick_value * 10

    @pip_value.setter
    def pip_value(self, value: float):
        self._pip_value: float = value

    @property
    def pip_size(self) -> float:
        return self.point_size * 10

    dynamic_leverage: list[LeverageTier] = []

    @property
    def market_hours(self) -> MarketHours:
        return MarketHours()

    def init_market_info(
        self, assets_path: str, symbol_name: str, market_values: MarketValues
    ) -> str:
        error = ""
        try:
            with open(assets_path, newline="") as csvfile:
                reader = csv.reader(csvfile)
                for line in reader:
                    if not line:
                        continue
                    line = [item.strip() for item in line]

                    if line[0] == "Name" and line[1] == "Price":
                        continue

                    if symbol_name != line[0]:
                        continue

                    if len(line) != 16:
                        return f"{assets_path} has wrong format (not 16 columns)"

                    market_values.symbol_name = symbol_name
                    market_values.swap_long = float(line[3])
                    market_values.swap_short = float(line[4])
                    market_values.point_size = float(line[5]) / 10.0
                    market_values.avg_spread = float(line[2]) / market_values.point_size
                    market_values.digits = int(
                        0.5 + math.log10(1 / market_values.point_size)
                    )
                    market_values.point_value = float(line[6]) / 10.0
                    market_values.margin_required = float(line[7])

                    market_time_split = line[8].split("-")
                    market_tzid_split = line[8].split(":")
                    market_values.symbol_tz_id = market_tzid_split[0].strip()
                    market_values.market_open_time = timedelta(
                        hours=int(market_tzid_split[1]),
                        minutes=int(market_tzid_split[2].split("-")[0]),
                    )
                    market_values.market_close_time = timedelta(
                        hours=int(market_time_split[1].split(":")[0]),
                        minutes=int(market_time_split[1].split(":")[1]),
                    )

                    market_values.min_volume = float(line[9])
                    market_values.max_volume = 10000 * market_values.min_volume
                    market_values.commission = float(line[10])
                    market_values.broker_symbol = line[11]
                    market_values.symbol_leverage = float(line[12])
                    market_values.lot_size = float(line[13])
                    market_values.symbol_currency_base = line[14].strip()
                    market_values.symbol_currency_quote = line[15].strip()
                    break
        except Exception as ex:
            error = str(ex)
            error += "\n" + traceback.format_exc()

        return error

    def update_bars(self, quote: QuoteBar):
        for bars in self.bars_list:
            bars.update_bar(quote)

        self.time = quote.time
        self.bid = quote.open
        self.ask = quote.open_ask

    def on_tick(self) -> str:
        error, quote = self.quote_provider.get_next_quote_bar()
        if None == quote:  # type: ignore
            return error
        # self.update_bars(quote)
        return ""


class Symbol(SymbolInfo):
    def __init__(
        self,
        symbol_name: str,
        assets_file_name: str,
        quote_provider: BrokerProvider,
        trade_provider: BrokerProvider,
    ):
        super().__init__(symbol_name, assets_file_name, quote_provider, trade_provider)

    ######################################
    @property
    def spread(self):
        return self.ask - self.bid

    def normalize_volume_in_units(
        self, volume: float, rounding_mode: RoundingMode = RoundingMode.ToNearest
    ) -> float:
        mod = volume % self.min_volume
        floor = volume - mod
        ceiling = floor + self.min_volume
        if RoundingMode.Up == rounding_mode:
            return ceiling

        elif RoundingMode.Down == rounding_mode:
            return floor

        else:
            return floor if volume - floor < ceiling - volume else ceiling

    def quantity_to_volume_in_units(self, quantity: float) -> float:
        return quantity * self.lot_size
        pass

    def volume_in_units_to_quantity(self, volume: float) -> float:
        return volume / self.lot_size
        pass


class Position:
    # Members
    # region
    symbol_name: str = ""
    symbol: Symbol = None  # type: ignore
    trade_type: TradeType = TradeType.Buy
    volume_in_units: float = 0
    id: int = 0
    gross_profit: float = 0
    entry_price: float = 0
    stop_loss: float = 0
    swap: float = 0
    commissions: float = 0
    entry_time: datetime = datetime.min
    closing_time: datetime = datetime.min
    pips: float = 0
    label: str = ""
    comment: str = ""
    quantity: float = 0
    has_trailing_stop: bool = False
    margin: float = 0
    stop_loss_trigger_method: StopTriggerMethod = StopTriggerMethod.Trade
    closing_price: float = 0
    max_drawdown: float = 0
    # endregion

    def __init__(self):
        pass

    def modify_stop_loss_price(self, stopLoss: float):
        """
        Shortcut for Robot.modify_position method to change the stop Loss price.
        """
        pass

    def modify_take_profit_price(self, takeProfit: float):
        """
        Shortcut for Robot.modify_position method to change the Take Profit price.
        """
        pass

    def modify_stop_loss_pips(self, stopLossPips: float):
        """
        Shortcut for the Robot.modify_position method to change the stop Loss in Pips.
        """
        pass

    def modify_take_profit_pips(self, takeProfitPips: float):
        """
        Shortcut for the Robot.modify_position method to change the Take Profit in Pips.
        """
        pass

    def modify_trailing_stop(self, hasTrailingstop: bool):
        """
        Shortcut for the Robot.modify_position method to change the Trailing stop.
        """
        pass

    def modify_volume(self, volume: float) -> TradeResult:
        """
        Shortcut for the Robot.modify_position method to change the volume_in_units.
        """
        trade_result = TradeResult()
        trade_result.is_successful = True
        return trade_result
        pass

    def reverse(self, volume: float = None):  # type: ignore
        """
        Shortcut for the Robot.reverse_position method to change the direction of the trade.
        """
        pass

    def close(self):
        """
        Shortcut for the Robot.close_position method.
        """
        pass

    @property
    def current_price(self):
        return self.symbol.bid if self.trade_type == TradeType.Buy else self.symbol.ask

    @property
    def net_profit(self) -> float:
        if 0 == self.id:  # MeFiles and Mt5 backtest
            if 0 == self.closing_price:
                # Position still open and in Positions queue
                return (
                    (self.current_price - self.entry_price)
                    * (1 if self.trade_type == TradeType.Buy else -1)
                    * self.volume_in_units
                )
            else:
                # Position closed and in History queue
                return (
                    (self.closing_price - self.entry_price)
                    * (1 if self.trade_type == TradeType.Buy else -1)
                    * self.volume_in_units
                )
        else:  # Mt5 live
            # import MetaTrader5 as mt5

            # mt5_pos = mt5.positions_get(ticket=self.id)
            # ret_val = mt5_pos[0].profit
            # return ret_val
            return 0


############# AlgoApi ########################
class AlgoApi:
    # Members
    # region
    # The following vars must be init from "above"
    start_dt: datetime
    end_dt: datetime
    running_mode: RunningMode
    robot_name: str
    account: Account
    # endregion

    def __init__(self):
        pass

    # Trading API
    # region
    def init_symbol(
        self,
        symbol_name: str,
        assets_file_name: str,
        quote_provider: BrokerProvider,
        trade_provider: BrokerProvider,
    ):
        symbol = Symbol(symbol_name, assets_file_name, quote_provider, trade_provider)
        self.symbol_dictionary[symbol_name] = symbol
        quote_provider.initialize(symbol_name)
        trade_provider.initialize(symbol_name)

    def get_bars(
        self, start_dt: datetime, timeframe_seconds: int, symbol_name: str
    ) -> Bars:
        new_bars = Bars(timeframe_seconds, symbol_name)
        symbol = self.symbol_dictionary[symbol_name]
        symbol.bars_list.append(new_bars)

        # build bars
        error, quote = symbol.quote_provider.get_quote_bar_at_date(start_dt)
        new_bars.update_bar(quote)

        while True:
            error, quote = symbol.quote_provider.get_next_quote_bar()
            if "" != error:
                break

            new_bars.update_bar(quote)
            if new_bars.open_times.count > 0 and quote.time >= start_dt:
                break
        pass
        return new_bars

    def close_trade(
        self,
        pos: Position,
        marginAfterOpen: float,
        min_open_duration: list[timedelta],
        avg_open_duration_sum: list[timedelta],
        open_duration_count: list[int],
        max_open_duration: list[timedelta],
        is_utc: bool = True,
    ) -> bool:
        close_result = self.close_position(pos)
        if close_result.is_successful:
            last_hist = self.history[-1]

            log = LogParams()
            log.symbol = pos.symbol
            log.volume_in_units = last_hist.volume_in_units
            log.trade_type = last_hist.trade_type
            log.closing_price = last_hist.closing_price
            log.entry_price = last_hist.entry_price
            log.entry_time = last_hist.entry_time
            log.closing_time = last_hist.closing_time
            log.net_profit = last_hist.net_profit
            log.comment = ""
            log.balance = self.Account.balance
            log.trade_margin = last_hist.margin
            log.max_equity_drawdown = self.max_equity_drawdown_value[0]
            # log.max_trade_equity_drawdown_value = self.max_trade_equity_drawdown_value[0]

            self.log_closing_trade(log)
            self.log_flush

            duration = last_hist.closing_time - last_hist.entry_time  # .seconds
            self.min_timedelta(min_open_duration, duration)
            avg_open_duration_sum[0] += duration
            open_duration_count[0] += 1
            self.max_timedelta(max_open_duration, duration)

            return True
        return False

    def execute_market_order(
        self, trade_type: TradeType, symbol_name: str, volume: float, label: str = ""
    ) -> Position:
        is_append_position = True  # default for Platforms.MeFiles

        pos = Position()
        pos.symbol_name = symbol_name
        pos.symbol = self.symbol_dictionary[symbol_name]
        pos.trade_type = trade_type
        pos.volume_in_units = volume
        pos.quantity = volume / pos.symbol.lot_size
        pos.entry_time = pos.symbol.time
        pos.entry_price = (
            pos.symbol.ask if TradeType.Buy == trade_type else pos.symbol.bid
        )
        pos.label = label
        pos.margin = volume * pos.entry_price / pos.symbol.leverage
        self.Account.margin += pos.margin

        if is_append_position:
            self.positions.append(pos)
        else:
            pos = None

        """
        self.chart.draw_icon(
            str(uuid.uuid4()),
            (
                ChartIconType.UpArrow
                if trade_type == TradeType.Buy
                else ChartIconType.DownArrow
            ),
            pos.entry_time,
            pos.entry_price,
            "blue" if trade_type == TradeType.Buy else "red",
        )
        """

        return pos  # pylint: disable=no-member # type: ignore

    def close_position(self, pos: Position):
        trade_result = TradeResult()
        try:
            self.Account.margin -= pos.margin
            pos.closing_price = pos.current_price
            pos.closing_time = pos.symbol.time
            self.history.append(pos)
            self.positions.remove(pos)
            self.Account.balance += pos.net_profit
            trade_result.is_successful = True
        except:
            pass

        return trade_result

    # endregion

    # Long/Short and other arithmetic
    # region
    def is_greater_or_equal_long(
        self, long_not_short: bool, val1: float, val2: float
    ) -> bool:
        return val1 >= val2 if long_not_short else val1 <= val2

    def is_less_or_equal_long(
        self, long_not_short: bool, val1: float, val2: float
    ) -> bool:
        return val1 <= val2 if long_not_short else val1 >= val2

    def is_greater_long(self, long_not_short: bool, val1: float, val2: float) -> bool:
        return val1 > val2 if long_not_short else val1 < val2

    def is_less_long(self, long_not_short: bool, val1: float, val2: float) -> bool:
        return val1 < val2 if long_not_short else val1 > val2

    def is_crossing(
        self,
        long_not_short: bool,
        a_current: float,
        a_prev: float,
        b_current: float,
        b_prev: float,
    ) -> bool:
        return self.is_greater_or_equal_long(
            long_not_short, a_current, b_current
        ) and self.is_less_or_equal_long(long_not_short, a_prev, b_prev)

    def add_long(self, long_not_short: bool, val1: float, val2: float) -> float:
        return val1 + val2 if long_not_short else val1 - val2

    def sub_long(self, long_not_short: bool, val1: float, val2: float) -> float:
        return val1 - val2 if long_not_short else val1 + val2

    def diff_long(self, long_not_short: bool, val1: float, val2: float) -> float:
        return val1 - val2 if long_not_short else val2 - val1

    def i_price(self, dPrice: float, tickSize: float) -> int:
        return int(math.copysign(0.5 + abs(dPrice) / tickSize, dPrice))

    def d_price(self, price: float, tickSize: float) -> float:
        return tickSize * price

    def max(self, ref_value: list[T], compare: T) -> bool:
        if compare > ref_value[0]:
            ref_value[0] = compare
            return True
        return False

    def min(self, ref_value: list[T], compare: T) -> bool:
        if compare < ref_value[0]:
            ref_value[0] = compare
            return True
        return False

    def max_timedelta(self, ref_value: list[timedelta], compare: timedelta) -> bool:
        if compare > ref_value[0]:
            ref_value[0] = compare
            return True
        return False

    def min_timedelta(self, ref_value: list[timedelta], compare: timedelta) -> bool:
        if compare < ref_value[0]:
            ref_value[0] = compare
            return True
        return False

    def sharpe_sortino(self, is_sortino: bool, vals: list[float]) -> float:
        if len(vals) < 2:
            return float("nan")

        average = sum(vals) / len(vals)
        sd = math.sqrt(
            sum((val - average) ** 2 for val in vals if not is_sortino or val < average)
            / (len(vals) - 1)
        )
        return average / sd if sd != 0 else float("nan")

    def standard_deviation(self, is_sortino: bool, vals: list[float]) -> float:
        average = sum(vals) / len(vals)
        return math.sqrt(
            sum((val - average) ** 2 for val in vals if not is_sortino or val < average)
            / (len(vals) - 1)
        )

    def is_new_bar_get(self, seconds: int, time: datetime, prevTime: datetime) -> bool:
        if datetime.min == prevTime:
            return True
        return int(time.timestamp()) // seconds != int(prevTime.timestamp()) // seconds

    # endregion

    # Logging
    # region
    logging_trade_count = 0

    @property
    def is_open(self) -> bool:
        return self.log_stream_writer is not None

    def open_logfile(
        self,
        filename: str = "",
        mode: int = PyLogger.HEADER_AND_SEVERAL_LINES,
        header: str = "",
    ):
        if self.running_mode != RunningMode.Optimization:
            self.logger = PyLogger()
            self.logger.log_open(
                self.logger.make_log_path(),
                filename,
                self.running_mode == RunningMode.RealTime,
                mode,
            )
            # if not openState:
            self.write_log_header(mode, header)

    def write_log_header(
        self,
        mode: int = PyLogger.HEADER_AND_SEVERAL_LINES,
        header: str = "",
    ):
        log_header: str = ""
        if (
            self.logger is None or not self.logger.is_open  # type: ignore
        ):  # or int(LoggerConstants.no_header) & int(self.logger.mode) != 0:
            return

        self.logger.add_text("sep =,")  # Hint for Excel

        if PyLogger.SELF_MADE == mode:
            log_header = header
        else:
            log_header += (
                "\nOpenDate,OpenTime,symbol,Lots,open_price,Swap,Swap/Lot,open_asks,open_bid,open_spread_pts"
                if 0 == (self.logger.mode & PyLogger.ONE_LINE)
                else ","
            )
            log_header += (
                ",CloseDate,ClosingTime,Mode,Volume,closing_price,commission,Comm/Lot,close_ask,close_bid,close_spread_pts"
                if 0 == (self.logger.mode & PyLogger.ONE_LINE)
                else ","
            )
            log_header += ",Number,Dur. d.h.self.s,Balance,point_value,diff_pts,diff_gross,net_profit,net_prof/Lot,account_margin,trade_margin"
            # if 0 == (self.logger.mode & one_line) log_header += (",\n")

        self.logger.add_text(log_header)
        self.logger.flush()
        self.header_split = log_header.split(",")

    def log_add_text(self, s: str):
        if self.logger is None or not self.logger.is_open:  # type: ignore
            return

        self.logger.add_text(s)

    def log_add_text_line(self, s: str):
        self.log_add_text(s + "\n")

    def log_closing_trade(self, lp: LogParams):
        if self.logger is None or not self.logger.is_open:  # type: ignore
            return

        # orgComment;123456,aaa,+-ppp     meaning:
        # openAskInPts,openSpreadInPts
        openBid, open_ask = 0, 0
        if lp.comment is not None:  # type: ignore
            bid_asks = lp.comment.split(";")
            if len(bid_asks) >= 2:
                bid_asks = bid_asks[1].split(",")
                if len(bid_asks) == 2:
                    i_ask = AlgoApi.string_to_integer(bid_asks[0])
                    open_ask = lp.symbol.point_size * i_ask
                    # open_bid = lp.symbol.point_size * (
                    #     i_ask - AlgoApi.string_to_integer(bid_asks[1])
                    # )

        price_diff = (1 if lp.trade_type == TradeType.Buy else -1) * (
            lp.closing_price - lp.entry_price
        )
        point_diff = self.i_price(price_diff, lp.symbol.point_size)
        lot_digits = 1  # int(0.5 + math.log10(1 / lp.min_lots))

        for part in self.header_split:
            change_part = part
            if "\n" in part:
                self.logger.add_text("\n")
                change_part = part[1:]
            else:
                self.logger.add_text(",")

            if change_part == "OpenDate":
                self.logger.add_text(lp.entry_time.strftime("%Y.%m.%d"))
                continue
            elif change_part == "OpenTime":
                self.logger.add_text(lp.entry_time.strftime("%H:%M:%S"))
                continue
            elif change_part == "Symbol":
                self.logger.add_text(lp.symbol.name)
                continue
            elif change_part == "Lots":
                self.logger.add_text(AlgoApi.double_to_string(lp.lots, lot_digits))
                continue
            elif change_part == "OpenPrice":
                self.logger.add_text(
                    AlgoApi.double_to_string(lp.entry_price, lp.symbol.digits)
                )
                continue
            elif change_part == "Swap":
                self.logger.add_text(AlgoApi.double_to_string(lp.swap, 2))
                continue
            elif change_part == "Swap/Lot":
                self.logger.add_text(AlgoApi.double_to_string(lp.swap / lp.lots, 2))
                continue
            elif change_part == "OpenAsks":
                self.logger.add_text(
                    AlgoApi.double_to_string(open_ask, lp.symbol.digits)
                    if lp.trade_type == TradeType.Buy
                    else ""
                )
                continue
            elif change_part == "OpenBid":
                self.logger.add_text(
                    AlgoApi.double_to_string(openBid, lp.symbol.digits)
                    if lp.trade_type == TradeType.Sell
                    else ""
                )
                continue
            elif change_part == "OpenSpreadPoints":
                self.logger.add_text(
                    AlgoApi.double_to_string(
                        self.i_price((open_ask - openBid), lp.symbol.point_size), 0
                    )
                )
                continue
            elif change_part == "CloseDate":
                self.logger.add_text(lp.closing_time.strftime("%Y.%m.%d"))
                continue
            elif change_part == "ClosingTime":
                self.logger.add_text(lp.closing_time.strftime("%H:%M:%S"))
                continue
            elif change_part == "Mode":
                self.logger.add_text(
                    "Short" if lp.trade_type == TradeType.Sell else "Long"
                )
                continue
            elif change_part == "PointValue":
                self.logger.add_text(
                    AlgoApi.double_to_string(
                        self.calc_1point_and_1lot_2money(lp.symbol), 5
                    )
                )
                continue
            elif change_part == "ClosingPrice":
                self.logger.add_text(
                    AlgoApi.double_to_string(lp.closing_price, lp.symbol.digits)
                )
                continue
            elif change_part == "Commission":
                self.logger.add_text(AlgoApi.double_to_string(lp.commissions, 2))
                continue
            elif change_part == "Comm/Lot":
                self.logger.add_text(
                    AlgoApi.double_to_string(lp.commissions / lp.lots, 2)
                )
                continue
            elif change_part == "CloseAsk":
                self.logger.add_text(
                    "{:.{}f}".format(
                        self.get_bid_ask_price(lp.symbol, BidAsk.Ask), lp.symbol.digits
                    )
                    if lp.trade_type == TradeType.Sell
                    else ""
                )
                continue
            elif change_part == "CloseBid":
                self.logger.add_text(
                    AlgoApi.double_to_string(
                        self.get_bid_ask_price(lp.symbol, BidAsk.Bid), lp.symbol.digits
                    )
                    if lp.trade_type == TradeType.Buy
                    else ""
                )
                continue
            elif change_part == "CloseSpreadPoints":
                self.logger.add_text(
                    AlgoApi.double_to_string(
                        self.i_price(
                            self.get_bid_ask_price(lp.symbol, BidAsk.Ask)
                            - self.get_bid_ask_price(lp.symbol, BidAsk.Bid),
                            lp.symbol.point_size,
                        ),
                        0,
                    )
                )
                continue
            elif change_part == "Balance":
                self.logger.add_text(AlgoApi.double_to_string(lp.balance, 2))
                continue
            elif change_part == "Dur. d.h.self.s":
                self.logger.add_text(
                    str(lp.entry_time - lp.closing_time).rjust(11, " ")
                )
                continue
            elif change_part == "Number":
                self.logging_trade_count += 1
                self.logger.add_text(
                    AlgoApi.integer_to_string(self.logging_trade_count)
                )
                continue
            elif change_part == "Volume":
                self.logger.add_text(AlgoApi.double_to_string(lp.volume_in_units, 1))
                continue
            elif change_part == "DiffPoints":
                self.logger.add_text(AlgoApi.double_to_string(point_diff, 0))
                continue
            elif change_part == "DiffGross":
                self.logger.add_text(
                    AlgoApi.double_to_string(
                        self.calc_points_and_lot_2money(lp.symbol, point_diff, lp.lots),
                        2,
                    )
                )
                continue
            elif change_part == "net_profit":
                self.logger.add_text(AlgoApi.double_to_string(lp.net_profit, 2))
                continue
            elif change_part == "NetProf/Lot":
                self.logger.add_text(
                    AlgoApi.double_to_string(lp.net_profit / lp.lots, 2)
                )
                continue
            elif change_part == "AccountMargin":
                self.logger.add_text(AlgoApi.double_to_string(lp.account_margin, 2))
                continue
            elif change_part == "TradeMargin":
                self.logger.add_text(AlgoApi.double_to_string(lp.trade_margin, 2))
                continue
            elif change_part == "MaxEquityDrawdown":
                self.logger.add_text(
                    AlgoApi.double_to_string(lp.max_equity_drawdown, 2)
                )
                continue
            elif change_part == "MaxTradeEquityDrawdownValue":
                self.logger.add_text(
                    AlgoApi.double_to_string(lp.max_trade_equity_drawdown_value, 2)
                )
                continue
            else:
                pass

        self.logger.flush()

    def log_flush(self):
        if self.logger is None or not self.logger.is_open:  # type: ignore
            return
        self.logger.flush()

    def log_close(self, header_line: str = ""):
        if self.logger is None or not self.logger.is_open:  # type: ignore
            return

        self.logger.close(header_line)
        self.log_stream_writer = None

    # endregion

    # Price and lot/volume calculation
    # region
    @staticmethod
    def get_bid_ask_price(symbol: Symbol, bidAsk: BidAsk):
        return symbol.bid if bidAsk == BidAsk.Bid else symbol.ask

    @staticmethod
    def calc_profitmode_2lots(
        symbol: Symbol,
        profitMode: ProfitMode,
        value: float,
        tpPts: int,
        riskPoints: int,
        desired_money: list[float],
        lot_size: list[float],
    ):
        desired_money[0] = 0
        lot_size[0] = 0

        if math.isnan(symbol.tick_value):
            return "Invalid tick_value"
        """
        if ProfitMode == ProfitMode.lots:
            desi_mon = self.calc_points_and_lot_2money(symbol: Symbol, tpPts, lot_siz =value)
        elif ProfitMode == ProfitMode.lots_pro10k:
            lot_siz = (self.Account.balance - self.Account.margin) / 10000 * value
            desi_mon = self.calc_points_and_lot_2money(symbol: Symbol, tpPts, lot_size)
        elif ProfitMode == ProfitMode.profit_percent:
            desi_mon = (self.Account.balance - self.Account.margin) * value / 100
            lot_siz = self.calc_money_and_points_2lots(symbol: Symbol, desired_money, tpPts, self.commission_per_lot(symbol: Symbol))
        elif ProfitMode == ProfitMode.profit_ammount:
            lot_siz = self.calc_money_and_points_2lots(symbol: Symbol, desi_mon =value, tp_pts =tpPts, x_pro_lot =self.commission_per_lot(symbol: Symbol))
        elif profitMode in [ProfitMode.risk_constant, ProfitMode.risk_reinvest]:
            balance = self.Account.balance if ProfitMode == ProfitMode.risk_reinvest else self.initial_account_balance
            money_to_risk = (balance - self.Account.margin) * value / 100
            lot_siz = self.calc_money_and_points_2lots(symbol: Symbol, moneyToRisk, riskPoints, self.commission_per_lot(symbol: Symbol))
            desi_mon = self.calc_points_and_lot_2money(symbol: Symbol, tpPts, lot_size)
        elif profitMode in [ProfitMode.constant_invest, ProfitMode.Reinvest]:
            invest_money = (self.initial_account_balance if ProfitMode == ProfitMode.constant_invest else self.Account.balance) * value / 100
            units = investMoney * symbol.point_size / symbol.tick_value / symbol.bid
            lot_siz = symbol.volume_in_units_to_quantity(units)
            desi_mon = self.calc_points_and_lot_2money(symbol: Symbol, tpPts, lot_size)
        """
        return ""

    @staticmethod
    def calc_points_and_lot_2money(symbol: Symbol, points: int, lot: float) -> float:
        return symbol.tick_value * symbol.lot_size * points * lot

    @staticmethod
    def calc_points_and_volume_2money(
        symbol: Symbol, points: int, volume: float
    ) -> float:
        return symbol.tick_value * points * volume / symbol.lot_size

    @staticmethod
    def calc_1point_and_1lot_2money(symbol: Symbol, reverse: bool = False):
        ret_val = AlgoApi.calc_points_and_lot_2money(symbol, 1, 1)
        if reverse:
            ret_val *= symbol.bid
        return ret_val

    @staticmethod
    def calc_money_and_lot_2points(symbol: Symbol, money: float, lot: float):
        return money / (lot * symbol.tick_value * symbol.lot_size)

    @staticmethod
    def calc_money_and_volume_2points(symbol: Symbol, money: float, volume: float):
        return money / (volume * symbol.tick_value)

    @staticmethod
    def calc_money_and_points_2lots(
        symbol: Symbol, money: float, points: int, xProLot: float
    ):
        ret_val = abs(money / (points * symbol.tick_value * symbol.lot_size + xProLot))
        ret_val = max(ret_val, symbol.min_volume)
        ret_val = min(ret_val, symbol.max_volume)
        return ret_val
        # endregion

    # Methods
    # region
    def load_class_from_file(self, file_path: str, class_name: str):
        # Load the module dynamically
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        spec = importlib.util.spec_from_file_location(module_name, file_path)  # type: ignore
        if spec is not None:
            module = importlib.util.module_from_spec(spec)  # type: ignore
            if spec.loader is not None:  # type: ignore
                spec.loader.exec_module(module)  # type: ignore

                # Retrieve the class from the module
                if hasattr(module, class_name):  # type: ignore
                    return getattr(module, class_name)  # type: ignore
                else:
                    raise AttributeError(f"Class {class_name} not found in {file_path}")
        return None  # type: ignore

    # def update_chart_text_and_bars(self):
    """
        self.BalanceValue.text = "{:.2f}".format(self.Account.balance)
        self.EquityValue.text = "{:.2f}".format(self.Account.equity)
        self.DatetimeValue.text = self.time.strftime("%d-%m-%Y %H:%M:%S")
        self.MaxEqDdValue.text = "{:.2f}".format(self.MaxEquityDrawdownValue[0])

        if self.bin_settings.is_visual_mode:
            if len(self.chart.x) != self.bin_settings.bars_in_chart:
                self.chart.x = np.arange(self.bin_settings.bars_in_chart)
                self.chart.x_open = self.chart.x - 0.4
                self.chart.x_close = self.chart.x + 0.4
            pass

            self.bars.ChartTimeArray = self.bars.open_times.data[
                -self.bin_settings.bars_in_chart :
            ]
            self.chart.source.data = {
                "x": self.chart.x,
                "x_open": self.chart.x_open,
                "x_close": self.chart.x_close,
                "lineColors": self.bars.LineColors[
                    -self.bin_settings.bars_in_chart :
                ],
                "times": self.bars.ChartTimeArray,
                "opens": self.bars.OpenPrices.data[
                    -self.bin_settings.bars_in_chart :
                ],
                "highs": self.bars.HighPrices.data[
                    -self.bin_settings.bars_in_chart :
                ],
                "lows": self.bars.LowPrices.data[-self.bin_settings.bars_in_chart :],
                "closes": self.bars.ClosePrices.data[
                    -self.bin_settings.bars_in_chart :
                ],
            }
        pass
    """

    def start(self):
        self.time: datetime = self.start_dt
        self.initial_time: datetime = self.start_dt
        self.initial_account_balance: float = self.account.balance
        self.symbol_dictionary: dict[str, Symbol] = {}  # type: ignore
        self.positions: list[Position] = []
        self.history: list[Position] = []
        self.max_equity_drawdown_value: list[float] = []
        self.is_train: bool = False
        self.max_margin = [0] * 1  # arrays because of by reference
        self.same_time_open = [0] * 1
        self.same_time_open_date_time = datetime.min
        self.same_time_open_count = 0
        self.max_balance = [0] * 1
        self.max_balance_drawdown_value = [0] * 1
        self.max_balance_drawdown_time = datetime.min
        self.max_balance_drawdown_count = 0
        self.max_equity: list[float] = [0] * 1
        self.max_equity_drawdown_value = [0] * 1
        self.max_equity_drawdown_time = datetime.min
        self.max_equity_drawdown_count = 0
        self.current_volume = 0
        self.initial_volume = 0
        self.min_open_duration: list[timedelta] = [timedelta.max] * 1
        self.avg_open_duration_sum: list[timedelta] = [timedelta.min] * 1
        self.open_duration_count: list[int] = [0] * 1  # arrays because of by reference
        self.max_open_duration: list[timedelta] = [timedelta.min] * 1

        self.loaded_robot = self.load_class_from_file(
            os.path.join("robots", self.robot_name + ".py"),
            self.robot_name,
        )
        self.loaded_robot.__init__(self)  # type: ignore

        self.loaded_robot.on_start(self)  # type: ignore

    def tick(self):
        # update quote, bars, Indicators
        # 1st tick must update all bars and Indicators which have been inized in on_start()
        for symbol in self.symbol_dictionary.values():
            error = symbol.on_tick()
            if "" != error or symbol.time > self.end_dt:
                return True

            ########################################
            # Update Account
            if len(self.positions) >= 1:
                symbol.trade_provider.update_account()

            # check spread
            is_spread = True
            if (
                symbol.spread < 0
                or symbol.spread
                > 2 * symbol.market_values.avg_spread * symbol.point_size
            ):
                is_spread = False
            symbol.is_trading_allowed = is_spread

            # call bot's on_tick
            self.loaded_robot.on_tick(symbol)  # type: ignore

            # do max/min calcs
            self.max(self.max_margin, self.Account.margin)
            if self.max(self.same_time_open, len(self.positions)):
                self.same_time_open_date_time = symbol.time
                self.same_time_open_count = len(self.history)

            self.max(self.max_balance, self.Account.balance)
            if self.max(
                self.max_balance_drawdown_value,
                self.max_balance[0] - self.Account.balance,
            ):
                self.max_balance_drawdown_time = symbol.time
                self.max_balance_drawdown_count = len(self.history)

            self.max(self.max_equity, self.Account.equity)
            if self.max(
                self.max_equity_drawdown_value, self.max_equity[0] - self.Account.equity
            ):
                self.max_equity_drawdown_time = symbol.time
                self.max_equity_drawdown_count = len(self.history)
            self.time = symbol.time

        return False

    def stop(self):
        # call bot
        self.loaded_robot.on_stop()  # type: ignore

        # calc performance numbers
        min_duration = timedelta.max
        max_duration = timedelta.min
        duration_count = 0
        max_invest_counter = [0] * 1
        # invest_count_histo = None
        duration_count += self.open_duration_count[0]
        min_duration = min(self.min_open_duration[0], min_duration)
        max_duration = max(self.max_open_duration[0], max_duration)
        self.loaded_robot.on_stop(self)  # type:ignore

        # self.max(self.max_invest_count[0], self.max_invest_count)

        # if direction == TradeDirection.Long == self.loaded_robot.longShorts[0].is_long:
        #     invest_count_histo = self.loaded_robot.longShorts[0].investCountHisto

        # if len(self.loaded_robot.longShorts) >= 2:
        #     if direction == TradeDirection.Long == self.loaded_robot.longShorts[1].is_long:
        #         invest_count_histo = self.loaded_robot.longShorts[1].investCountHisto

        winning_trades = len([x for x in self.history if x.net_profit >= 0])
        loosing_trades = len([x for x in self.history if x.net_profit < 0])
        net_profit = sum(x.net_profit for x in self.history)
        trading_days = (  # 365 - 2*52 = 261 - 9 holidays = 252
            (self.time - self.initial_time).days / 365.0 * 252.0
        )
        if 0 == trading_days:
            annual_profit = 0
        else:
            annual_profit = net_profit / (trading_days / 252.0)
        total_trades = winning_trades + loosing_trades
        annual_profit_percent = (
            0
            if total_trades == 0
            else 100.0 * annual_profit / self.initial_account_balance
        )
        loss = sum(x.net_profit for x in self.history if x.net_profit < 0)
        profit = sum(x.net_profit for x in self.history if x.net_profit >= 0)
        profit_factor = 0 if loosing_trades == 0 else abs(profit / loss)
        max_current_equity_dd_percent = (
            100 * self.max_equity_drawdown_value[0] / self.max_equity[0]
        )
        max_start_equity_dd_percent = (
            100 * self.max_equity_drawdown_value[0] / self.initial_account_balance
        )
        calmar = (
            0
            if self.max_equity_drawdown_value[0] == 0
            else annual_profit / self.max_equity_drawdown_value[0]
        )
        winning_ratio_percent = (
            0 if total_trades == 0 else 100.0 * winning_trades / total_trades
        )

        if 0 == trading_days:
            trades_per_month = 0
        else:
            trades_per_month = total_trades / (trading_days / 252.0) / 12.0

        sharpe_ratio = self.sharpe_sortino(
            False, [trade.net_profit for trade in self.history]
        )
        sortino_ratio = self.sharpe_sortino(
            True, [trade.net_profit for trade in self.history]
        )

        # some proofs
        # percent_sharpe_ratio = self.sharpe_sortino(
        #     False,
        #     [trade.net_profit / self.initial_account_balance for trade in self.history],
        # )

        # vals = [trade.net_profit for trade in self.history]
        # average = sum(vals) / len(vals)
        # sd = self.standard_deviation(False, vals)
        # # my_sharpe = average / sd
        # # Baron
        # average_daily_return = annual_profit / 252.0
        # sharpe_ratio = average_daily_return / sd * sqrt(252.0)

        self.log_add_text_line("")
        self.log_add_text_line("")
        self.log_add_text_line(
            "Net Profit,"
            + AlgoApi.double_to_string(profit + loss, 2)
            + ",,,,Long: "
            + AlgoApi.double_to_string(
                sum(
                    x.net_profit for x in self.history if x.trade_type == TradeType.Buy
                ),
                2,
            )
            + ",,,,Short:,"
            + AlgoApi.double_to_string(
                sum(
                    x.net_profit for x in self.history if x.trade_type == TradeType.Sell
                ),
                2,
            )
        )

        # self.log_add_text_line("max_margin: " + self.Account.asset + " " + AlgoApi.double_to_string(mMaxMargin, 2))
        # self.log_add_text_line("max_same_time_open: " + str(mSameTimeOpen)
        # + ", @ " + mSameTimeOpenDateTime.strftime("%d.%m.%Y %H:%M:%S")
        # + ", Count# " + str(mSameTimeOpenCount))
        self.log_add_text_line(
            "Max Balance Drawdown Value: "
            + self.Account.asset
            + " "
            + AlgoApi.double_to_string(self.max_balance_drawdown_value[0], 2)
            + "; @ "
            + self.max_balance_drawdown_time.strftime("%d.%m.%Y %H:%M:%S")
            + "; Count# "
            + str(self.max_balance_drawdown_count)
        )

        self.log_add_text_line(
            "Max Balance Drawdown%: "
            + (
                "NaN"
                if self.max_balance[0] == 0
                else AlgoApi.double_to_string(
                    100 * self.max_balance_drawdown_value[0] / self.max_balance[0], 2
                )
            )
        )

        self.log_add_text_line(
            "Max Equity Drawdown Value: "
            + self.Account.asset
            + " "
            + AlgoApi.double_to_string(self.max_equity_drawdown_value[0], 2)
            + "; @ "
            + self.max_equity_drawdown_time.strftime("%d.%m.%Y %H:%M:%S")
            + "; Count# "
            + str(self.max_equity_drawdown_count)
        )

        self.log_add_text_line(
            "Max Current Equity Drawdown %: "
            + AlgoApi.double_to_string(max_current_equity_dd_percent, 2)
        )

        self.log_add_text_line(
            "Max start Equity Drawdown %: "
            + AlgoApi.double_to_string(max_start_equity_dd_percent, 2)
        )

        self.log_add_text_line(
            "Profit Factor: "
            + (
                "-"
                if loosing_trades == 0
                else AlgoApi.double_to_string(profit_factor, 2)
            )
        )

        self.log_add_text_line(
            "Sharpe Ratio: " + AlgoApi.double_to_string(sharpe_ratio, 2)
        )
        self.log_add_text_line(
            "Sortino Ratio: " + AlgoApi.double_to_string(sortino_ratio, 2)
        )

        self.log_add_text_line("Calmar Ratio: " + AlgoApi.double_to_string(calmar, 2))
        self.log_add_text_line(
            "Winning Ratio: " + AlgoApi.double_to_string(winning_ratio_percent, 2)
        )

        self.log_add_text_line(
            "Trades Per Month: " + AlgoApi.double_to_string(trades_per_month, 2)
        )

        self.log_add_text_line(
            "Average Annual Profit Percent: "
            + AlgoApi.double_to_string(annual_profit_percent, 2)
        )

        # if avg_open_duration_sum != 0:
        #     self.log_add_text_line(
        #         "Min / Avg / Max Tradeopen Duration (Day.Hour.Min.sec): "
        #         + str(min_duration)
        #         + " / "
        #         + str(avg_open_duration_sum / avg_open_duration_sum)
        #         + " / "
        #         + str(self.max_duration)
        #     )
        self.log_add_text_line("Max Repurchase: " + str(max_invest_counter[0]))
        # histo_rest_sum = 0.0
        # if investCountHisto is not None:
        #     for i in range(len(investCountHisto) - 1, 0, -1):
        #         if investCountHisto[i] != 0:
        #             self.log_add_text_line("Invest " + str(i) + ": " + str(investCountHisto[i]))
        #             if i > 1:
        #                 histoRestSum += investCountHisto[i]
        #     if histoRestSum != 0:
        #         self.log_add_text_line("histo_rest_quotient: " + AlgoApi.double_to_string(m_histo_rest_quotient = investCountHisto[1] / histoRestSum,
        self.log_close()

    def calculate_reward(self) -> float:
        return self.loaded_robot.get_tick_fitness()  # type:ignore

    # endregion

    #
    @staticmethod
    def double_to_string(value: float, digits: int) -> str:
        if value == float("inf") or value != value:
            return "NaN"
        format_str = "{:." + str(digits) + "f}"
        return format_str.format(value)

    @staticmethod
    def integer_to_string(n: int) -> str:
        return str(n)

    @staticmethod
    def string_to_double(s: str) -> float:
        try:
            return locale.atof(s)
        except ValueError:
            return 0

    @staticmethod
    def string_to_integer(s: str) -> int:
        try:
            return int(s)
        except ValueError:
            return 0


############# Classes using AlgoApi ########################
class HedgePosition:
    # Member variables
    # region
    main_id: str = "Main;"
    reverse_id: str = "Reverse;"
    main_freeze_id: str = "main_freeze;"
    weekend_freeze_id: str = "weekend_freeze;"
    main_position: Position = None  # type: ignore
    freeze_position: Position = None  # type: ignore
    is_profit_earned: bool = False
    freeze_open_bar_count: int = 0
    freeze_corrected_entry_price: float = 0
    main_margin_after_open: float = 0
    freeze_margin_after_open: float = 0
    freeze_profit_offset: float = 0
    freeze_price_offset: float = 0
    last_modified_time: datetime = datetime.min
    bot: AlgoApi

    @property
    def profit(self) -> float:
        return round(
            self.main_position.net_profit
            + self.freeze_position.net_profit
            + self.freeze_profit_offset,
            2,
        )

    @property
    def max_volume(self) -> float:
        if self.main_position is not None and self.freeze_position is not None:  # type: ignore
            return max(
                self.main_position.volume_in_units,
                self.freeze_position.volume_in_units,
            )
        elif self.main_position is not None:  # type: ignore
            return self.main_position.volume_in_units
        elif self.freeze_position is not None:  # type: ignore
            return self.freeze_position.volume_in_units
        else:
            return 0

    # endregion

    def __init__(self, algo_api: AlgoApi, symbol: Symbol, is_long: bool, label: str):
        self.bot = algo_api
        self.symbol = symbol
        self.is_long = is_long
        self.label = label

    def do_freeze_open(self, volume: float = 0) -> bool:
        if self.freeze_position is None:  # type: ignore
            return self.do_freeze(self.main_freeze_id, volume)
        else:
            return False

    def do_main_open(
        self,
        volume: float,
        inherited_freeze_price_offset: float = 0,
        label_ext: str = main_id,
    ) -> bool:
        if self.main_position is None:  # type: ignore
            self.main_position = self.bot.execute_market_order(
                TradeType.Buy if self.is_long else TradeType.Sell,
                self.symbol.name,
                self.symbol.normalize_volume_in_units(volume),
                self.label + label_ext,
            )

            if self.main_position is not None:  # type: ignore
                pass
                self.main_margin_after_open = (
                    self.symbol.trade_provider.account.margin  # type:ignore
                )
                self.freeze_price_offset = inherited_freeze_price_offset
                self.freeze_corrected_entry_price = (
                    self.main_position.entry_price  # type:ignore
                )

        return self.main_position is not None  # type: ignore

    def do_main_close(
        self,
        min_open_duration: list[timedelta],
        avg_open_duration_sum: list[timedelta],
        open_duration_count: list[int],
        max_open_duration: list[timedelta],
        is_utc: bool = True,
    ) -> bool:
        result = False
        if self.main_position is not None:  # type: ignore
            result = self.bot.close_trade(
                self.main_position,
                self.main_margin_after_open,
                min_open_duration,
                avg_open_duration_sum,
                open_duration_count,
                max_open_duration,
                is_utc,
            )
            self.main_position = None  # type: ignore
        return result

    def do_modify_volume(self, volume: float, current_open_price: float) -> bool:
        self.last_modified_time = self.symbol.time
        self.freeze_corrected_entry_price = current_open_price
        if self.main_position is not None:  # type: ignore
            return self.main_position.modify_volume(volume).is_successful
        return False

        self.open_duration_count = [0] * 1  # arrays because of by reference
        self.min_open_duration = [timedelta.max] * 1
        self.avg_open_duration_sum = [timedelta.min] * 1
        self.max_open_duration = [timedelta.min] * 1

    def do_freeze_close(
        self,
        min_open_duration: list[timedelta],
        avg_open_duration_sum: list[timedelta],
        open_duration_count: list[int],
        max_open_duration: list[timedelta],
        is_utc: bool = True,
    ) -> bool:
        result = False
        if self.freeze_position is not None:  # type: ignore
            self.freeze_profit_offset += self.freeze_position.net_profit
            self.freeze_price_offset += (
                self.freeze_position.current_price - self.freeze_position.entry_price
            )
            result = self.bot.close_trade(
                self.freeze_position,
                self.freeze_margin_after_open,
                min_open_duration,
                avg_open_duration_sum,
                open_duration_count,
                max_open_duration,
                is_utc,
            )
            self.freeze_position = None  # type: ignore
        return result

    def do_exchange_and_freeze_close(
        self,
        min_open_duration: list[timedelta],
        avg_open_duration_sum: list[timedelta],
        open_duration_count: list[int],
        max_open_duration: list[timedelta],
        is_utc: bool = True,
    ) -> bool:
        result = False
        if self.freeze_position is not None:  # type: ignore
            self.freeze_price_offset += (
                self.freeze_position.current_price - self.freeze_position.entry_price
            )
            self.exchange()
            self.freeze_profit_offset += self.freeze_position.net_profit
            result = self.bot.close_trade(
                self.freeze_position,
                self.freeze_margin_after_open,
                min_open_duration,
                avg_open_duration_sum,
                open_duration_count,
                max_open_duration,
                is_utc,
            )
            self.freeze_position = None  # type: ignore
        return result

    def do_both_close(
        self,
        min_open_duration: list[timedelta],
        avg_open_duration_sum: list[timedelta],
        open_duration_count: list[int],
        max_open_duration: list[timedelta],
        is_utc: bool = True,
    ) -> bool:
        if self.main_position is None and self.freeze_position is None:  # type: ignore
            return False

        if self.main_position is not None:  # type: ignore
            self.do_main_close(
                min_open_duration,
                avg_open_duration_sum,
                open_duration_count,
                max_open_duration,
                is_utc,
            )
            self.main_position = None  # type: ignore

        if self.freeze_position is not None:  # type: ignore
            self.do_freeze_close(
                min_open_duration,
                avg_open_duration_sum,
                open_duration_count,
                max_open_duration,
                is_utc,
            )
            self.freeze_position = None  # type: ignore

        return True

    def close_frozen_and_modify_main(
        self,
        volume: float,
        min_open_duration: list[timedelta],
        avg_open_duration_sum: list[timedelta],
        open_duration_count: list[int],
        max_open_duration: list[timedelta],
        is_utc: bool = True,
    ) -> bool:
        ret_val = False
        if self.main_position is None or self.freeze_position is None:  # type: ignore
            return ret_val

        self.main_position.modify_volume(volume)
        ret_val = self.do_freeze_close(
            min_open_duration,
            avg_open_duration_sum,
            open_duration_count,
            max_open_duration,
            is_utc,
        )
        self.freeze_position = None  # type: ignore

        return ret_val

    def close_main_and_modify_frozen(
        self,
        volume: float,
        min_open_duration: list[timedelta],
        avg_open_duration_sum: list[timedelta],
        open_duration_count: list[int],
        max_open_duration: list[timedelta],
        is_utc: bool = True,
    ) -> bool:
        ret_val = False
        if self.main_position is None or self.freeze_position is None:  # type: ignore
            return ret_val

        self.freeze_position.modify_volume(volume)
        ret_val = self.do_main_close(
            min_open_duration,
            avg_open_duration_sum,
            open_duration_count,
            max_open_duration,
            is_utc,
        )
        self.main_position = None  # type: ignore

        return ret_val

    def reverse(
        self,
        volume: float,
        min_open_duration: list[timedelta],
        avg_open_duration_sum: list[timedelta],
        open_duration_count: list[int],
        max_open_duration: list[timedelta],
        is_utc: bool = True,
    ) -> bool:
        ret_val = False
        if (
            self.main_position is None  # type: ignore
            and self.freeze_position is None  # type: ignore
            or self.main_position is not None  # type: ignore
            and self.freeze_position is not None  # type: ignore
        ):
            return ret_val

        if self.freeze_position is not None:  # type: ignore
            self.do_freeze_close(
                min_open_duration,
                avg_open_duration_sum,
                open_duration_count,
                max_open_duration,
                is_utc,
            )
            self.freeze_position = None  # type: ignore
        else:
            self.do_main_close(
                min_open_duration,
                avg_open_duration_sum,
                open_duration_count,
                max_open_duration,
                is_utc,
            )
            self.is_long = not self.is_long

        ret_val = self.do_main_open(volume, self.freeze_price_offset, self.reverse_id)
        return ret_val

    def exchange(self) -> bool:
        if self.main_position is None or self.freeze_position is None:  # type: ignore
            return False

        backup = self.main_position
        self.main_position = self.freeze_position
        self.freeze_position = backup

        return True

    def do_week_end_freeze(self, volume: float = 0) -> bool:
        if self.freeze_position is None:  # type: ignore
            return self.do_freeze(self.weekend_freeze_id, volume)
        else:
            return False

    def do_freeze(self, label_extension: str, volume: float) -> bool:
        result = None
        if self.freeze_position is None:  # type: ignore
            result = self.bot.execute_market_order(
                TradeType.Buy if self.is_long else TradeType.Sell,
                self.symbol.name,
                self.symbol.normalize_volume_in_units(volume),
                self.label + label_extension,
            )

            if result is not None:  # type: ignore
                self.freeze_position = result
                self.freeze_margin_after_open = self.bot.Account.margin
        return self.freeze_position is not None  # type: ignore


# end of file