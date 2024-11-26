import os
import math
import importlib.util
import importlib
import numpy as np
from abc import ABC, abstractmethod
from numpy.typing import NDArray
from typing import TypeVar, Iterable, Iterator
from datetime import datetime, timedelta, timezone

from ConvertUtils import ConvertUtils
from Account import Account
from PyLogger import PyLogger
from TradeResult import TradeResult
from Settings import BinSettings
from Asset import Asset
from QuoteBar import QuoteBar
from LeverageTier import LeverageTier
from MarketHours import MarketHours
from LogParams import LogParams
from AlgoApiEnums import *
from CoFu import *


# Define a TypeVar that can be float or int
T = TypeVar("T", float, int)


# Due to circular import problmes with separated classe, we define them here
class MarketValues:
    def __init__(self):
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
        self.min_lot = 0.0
        self.max_lot = 0.0
        self.lot_size = 0.0
        self.commission = 0.0
        self.broker_symbol = ""
        self.symbol_leverage = 0.0
        self.symbol_currency_base = ""
        self.symbol_currency_quote = ""


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
    # # region
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
    #         bars = self.algo_api.bars

    #     pass

    # def true_range(self, bars):
    #     # True Range indicator instance with bars
    #     if None == bars:
    #         bars = self.algo_api.bars

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
    #         bars = self.algo_api.bars

    #     pass

    # def williams_accumulation_distribution(self, bars):
    #     # Williams Accumulation Distribution indicator instance with bars
    #     if None == bars:
    #         bars = self.algo_api.bars

    #     pass

    # def fractal_chaos_bands(self, bars):
    #     # Fractal Chaos Bands indicator instance with bars
    #     if None == bars:
    #         bars = self.algo_api.bars

    #     pass

    # def typical_price(self, bars):
    #     # Typical Price indicator instance with bars
    #     if None == bars:
    #         bars = self.algo_api.bars

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
    #         bars = self.algo_api.bars

    #     pass

    # def chaikin_money_flow(self, bars: Bars, periods: int):
    #     # Chaikin Money Flow indicator instance with bars
    #     pass

    # def ease_of_movement(self, periods: int, ma_type):
    #     # Ease Of Movement indicator instance
    #     bars = self.algo_api.bars

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
        if 0 == self.open_times.count or self.algo_api.is_new_bar(
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


class SymbolInfo:
    # Members
    # region
    name: str = ""
    bars_list: list[Bars] = []
    time: datetime = datetime.min
    bid: float = 0
    ask: float = 0
    broker_symbol_name: str = ""
    min_lot: float = 0.0
    max_lot: float = 0.0
    lot_size: float = 0.0
    # endregion

    def __init__(self, symbol_name: str):
        self.name = symbol_name

    @property
    def tick_size(self) -> float:
        return self._tick_size

    @tick_size.setter
    def tick_size(self, value: float):
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
        return self.tick_size * 10

    dynamic_leverage: list[LeverageTier] = []

    @property
    def MarketHours(self) -> MarketHours:
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

                    market_values.min_lot = float(line[9])
                    market_values.max_lot = 10000 * market_values.min_lot
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

    # def on_tick(self) -> str:
    #     error, quote = self.quote_provider.get_next_quote()
    #     if None == quote:
    #         return error
    #     self.update_bars(quote)
    #     return ""


class Symbol(SymbolInfo):
    def __init__(self, symbol_name: str):
        super().__init__(symbol_name)

    ######################################
    @property
    def spread(self):
        return self.ask - self.bid

    def normalize_volume_in_units(
        self, volume: float, rounding_mode: RoundingMode = RoundingMode.ToNearest
    ) -> float:
        mod = volume % self.min_lot
        floor = volume - mod
        ceiling = floor + self.min_lot
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


class AlgoApi:
    # Members
    # region
    # endregion

    def __init__(self):
        system_settings: StrSettings = None  # type: ignore

        settings_path = os.path.join("Files", "System.json")
        error, self.system_settings = CoFu.load_settings(settings_path)
        if "" != error:
            # create empty sttings file
            self.system_settings = StrSettings(
                "1",
                "2",
                "3",
                "4",
                "5",
                "6",
                "7",
                "8",
                "9",
                "10",
                "11",
                "12",
                "13",
                "14",
            )

        self.symbol_dictionary: dict[str, Symbol] = {}  # type: ignore
        self.symbol_list: list[Symbol] = []
        self.positions: list[Position] = []
        self.history: list[Position] = []
        self.max_equity_drawdown_value: list[float] = []
        self.time: datetime
        self.running_mode: RunningMode
        self.logger: PyLogger = None  # type: ignore
        self.is_train: bool
        self.bin_settings = BinSettings(
            robot_name=self.system_settings.robot_name,
            default_symbol_name=self.system_settings.default_symbol_name,
            default_timeframe_seconds=self.get_timeframe_from_gui_params(
                self.system_settings
            ),
            trade_direction=TradeDirection[self.system_settings.trade_direction],
            init_balance=float(self.system_settings.init_balance),
            start_dt=(
                datetime.strptime(self.system_settings.start_dt, "%Y-%m-%d")
            ).replace(tzinfo=timezone.utc),
            end_dt=(datetime.strptime(self.system_settings.end_dt, "%Y-%m-%d")).replace(
                tzinfo=timezone.utc
            ),
            is_visual_mode=self.system_settings.is_visual_mode == "True",
            speed=int(self.system_settings.speed),
            bars_in_chart=int(self.system_settings.chart_bars),
            data_rate=DataRates[self.system_settings.data_rate],
            platform=Platforms[self.system_settings.platform],
            platform_parameter=self.system_settings.platform_parameter,
        )
        self.max_margin = [0] * 1  # arrays because of by reference
        self.same_time_open = [0] * 1
        self.same_time_open_date_time = datetime.min
        self.same_time_open_count = 0
        self.max_balance = [0] * 1
        self.max_balance_drawdown_value = [0] * 1
        self.max_balance_drawdown_time = datetime.min
        self.max_balance_drawdown_count = 0
        self.max_equity = [0] * 1
        self.max_equity_drawdown_value = [0] * 1
        self.max_equity_drawdown_time = datetime.min
        self.max_equity_drawdown_count = 0
        self.current_volume = 0
        self.initial_volume = 0
        self.min_open_duration: list[timedelta] = [timedelta.max] * 1
        self.avg_open_duration_sum: list[timedelta] = [timedelta.min] * 1
        self.open_duration_count: list[int] = [0] * 1  # arrays because of by reference
        self.max_open_duration: list[timedelta] = [timedelta.min] * 1
        self.is_trading_allowed: bool = False

        self.loaded_robot = self.load_class_from_file(
            os.path.join("robots", self.system_settings.robot_name + ".py"),
            self.system_settings.robot_name,
        )
        self.loaded_robot.__init__(self)  # type: ignore

        self.Account = Account()
        pass

    # Trading API
    # region
    ###################################
    def get_symbol(self, symbol_name: str):
        ret_val = Symbol(symbol_name)
        self.symbol_dictionary[symbol_name] = ret_val
        self.symbol_list.append(ret_val)
        return ret_val

    ###################################
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

    ###################################
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
        pos.entry_time = self.time
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

    ###################################
    def close_position(self, pos: Position):
        trade_result = TradeResult()
        try:
            self.Account.margin -= pos.margin
            pos.closing_price = pos.current_price
            pos.closing_time = self.time
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

    def is_new_bar(self, seconds: int, time: datetime, prevTime: datetime) -> bool:
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
        logger: PyLogger,
        filename: str = "",
        mode: int = PyLogger.HEADER_AND_SEVERAL_LINES,
        header: str = "",
    ):
        if self.running_mode != RunningMode.Optimization:
            if self.logger is not None:  # type: ignore
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
                    i_ask = ConvertUtils.string_to_integer(bid_asks[0])
                    open_ask = lp.symbol.tick_size * i_ask
                    # open_bid = lp.symbol.tick_size * (
                    #     i_ask - ConvertUtils.string_to_integer(bid_asks[1])
                    # )

        price_diff = (1 if lp.trade_type == TradeType.Buy else -1) * (
            lp.closing_price - lp.entry_price
        )
        point_diff = self.i_price(price_diff, lp.symbol.tick_size)
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
                self.logger.add_text(ConvertUtils.double_to_string(lp.lots, lot_digits))
                continue
            elif change_part == "OpenPrice":
                self.logger.add_text(
                    ConvertUtils.double_to_string(lp.entry_price, lp.symbol.digits)
                )
                continue
            elif change_part == "Swap":
                self.logger.add_text(ConvertUtils.double_to_string(lp.swap, 2))
                continue
            elif change_part == "Swap/Lot":
                self.logger.add_text(
                    ConvertUtils.double_to_string(lp.swap / lp.lots, 2)
                )
                continue
            elif change_part == "OpenAsks":
                self.logger.add_text(
                    ConvertUtils.double_to_string(open_ask, lp.symbol.digits)
                    if lp.trade_type == TradeType.Buy
                    else ""
                )
                continue
            elif change_part == "OpenBid":
                self.logger.add_text(
                    ConvertUtils.double_to_string(openBid, lp.symbol.digits)
                    if lp.trade_type == TradeType.Sell
                    else ""
                )
                continue
            elif change_part == "OpenSpreadPoints":
                self.logger.add_text(
                    ConvertUtils.double_to_string(
                        self.i_price((open_ask - openBid), lp.symbol.tick_size), 0
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
                    ConvertUtils.double_to_string(
                        self.calc_1point_and_1lot_2money(lp.symbol), 5
                    )
                )
                continue
            elif change_part == "ClosingPrice":
                self.logger.add_text(
                    ConvertUtils.double_to_string(lp.closing_price, lp.symbol.digits)
                )
                continue
            elif change_part == "Commission":
                self.logger.add_text(ConvertUtils.double_to_string(lp.commissions, 2))
                continue
            elif change_part == "Comm/Lot":
                self.logger.add_text(
                    ConvertUtils.double_to_string(lp.commissions / lp.lots, 2)
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
                    ConvertUtils.double_to_string(
                        self.get_bid_ask_price(lp.symbol, BidAsk.Bid), lp.symbol.digits
                    )
                    if lp.trade_type == TradeType.Buy
                    else ""
                )
                continue
            elif change_part == "CloseSpreadPoints":
                self.logger.add_text(
                    ConvertUtils.double_to_string(
                        self.i_price(
                            self.get_bid_ask_price(lp.symbol, BidAsk.Ask)
                            - self.get_bid_ask_price(lp.symbol, BidAsk.Bid),
                            lp.symbol.tick_size,
                        ),
                        0,
                    )
                )
                continue
            elif change_part == "Balance":
                self.logger.add_text(ConvertUtils.double_to_string(lp.balance, 2))
                continue
            elif change_part == "Dur. d.h.self.s":
                self.logger.add_text(
                    str(lp.entry_time - lp.closing_time).rjust(11, " ")
                )
                continue
            elif change_part == "Number":
                self.logging_trade_count += 1
                self.logger.add_text(
                    ConvertUtils.integer_to_string(self.logging_trade_count)
                )
                continue
            elif change_part == "Volume":
                self.logger.add_text(
                    ConvertUtils.double_to_string(lp.volume_in_units, 1)
                )
                continue
            elif change_part == "DiffPoints":
                self.logger.add_text(ConvertUtils.double_to_string(point_diff, 0))
                continue
            elif change_part == "DiffGross":
                self.logger.add_text(
                    ConvertUtils.double_to_string(
                        self.calc_points_and_lot_2money(lp.symbol, point_diff, lp.lots),
                        2,
                    )
                )
                continue
            elif change_part == "net_profit":
                self.logger.add_text(ConvertUtils.double_to_string(lp.net_profit, 2))
                continue
            elif change_part == "NetProf/Lot":
                self.logger.add_text(
                    ConvertUtils.double_to_string(lp.net_profit / lp.lots, 2)
                )
                continue
            elif change_part == "AccountMargin":
                self.logger.add_text(
                    ConvertUtils.double_to_string(lp.account_margin, 2)
                )
                continue
            elif change_part == "TradeMargin":
                self.logger.add_text(ConvertUtils.double_to_string(lp.trade_margin, 2))
                continue
            elif change_part == "MaxEquityDrawdown":
                self.logger.add_text(
                    ConvertUtils.double_to_string(lp.max_equity_drawdown, 2)
                )
                continue
            elif change_part == "MaxTradeEquityDrawdownValue":
                self.logger.add_text(
                    ConvertUtils.double_to_string(lp.max_trade_equity_drawdown_value, 2)
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
            units = investMoney * symbol.tick_size / symbol.tick_value / symbol.bid
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
        ret_val = max(ret_val, symbol.min_lot)
        ret_val = min(ret_val, symbol.max_lot)
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

    def get_timeframe_from_gui_params(self, settings: StrSettings) -> int:
        value = int(settings.default_timeframe_value)
        tf = TimeframeUnits[self.system_settings.default_timeframe_unit]
        ret_val = value
        if TimeframeUnits.Min == tf:
            ret_val = value * 60
        elif TimeframeUnits.Hour == tf:
            ret_val = value * 3600
        elif TimeframeUnits.Day == tf:
            ret_val = value * 3600 * 24
        elif TimeframeUnits.Week == tf:
            ret_val = value * 3600 * 24 * 7
        return ret_val

        def get_bars(self, timeframe_seconds: int, symbol_name: str) -> Bars:
            new_bars = Bars(self.algo_api, timeframe_seconds, symbol_name)
            symbol = self.algo_api.symbol_dictionary[symbol_name]
            symbol.bars_list.append(new_bars)

            # build bars
            # bars_start_dt = self.algo_api.bin_settings.start_dt - timedelta(
            #     seconds=1000 * timeframe_seconds
            # )
            # error, quote = symbol.quote_provider.get_quote_at_date(bars_start_dt)
            # new_bars.update_bar(quote)

            # while True:
            #     error, quote = symbol.quote_provider.get_next_quote()
            #     if "" != error:
            #         break

            #     new_bars.update_bar(quote)
            #     if (
            #         new_bars.open_times.count > 0
            #         and quote.time >= self.algo_api.bin_settings.start_dt
            #     ):
            #         break
            pass
            return new_bars

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

    def pre_start(self):
        # Init member variables
        # region
        self.initial_time = self.time = self.prev_time = self.bin_settings.start_dt
        self.initial_account_balance = self.Account.equity = self.Account.balance = (
            self.bin_settings.init_balance
        )
        self.trade_direction = self.bin_settings.trade_direction

        self.running_mode = (
            RunningMode.VisualBacktesting
            if self.bin_settings.is_visual_mode
            else RunningMode.SilentBacktesting
        )
        self.is_stop = False
        self.bars = None
        # endregion

        # Init default symbol
        self.symbol = self.get_symbol(self.bin_settings.default_symbol_name)

        # Init default bars (needed for chart if visible)
        if self.bin_settings.bars_in_chart > 0:
            self.bars = self.market_data.get_bars(
                self.bin_settings.default_timeframe_seconds, self.symbol.name
            )

        # H�here Entropiewerte bedeuten, dass die Datenquelle weniger vorhersehbar
        # und zuf�lliger ist. Umgekehrt bedeuten niedrigere Entropiewerte,
        # dass die Datenquelle vorhersehbarer und weniger zuf�llig ist.

        """
        # Generate a random price series
        price_series = np.randoself.normal(1, 0.2, 100000)

        # Calculate the probability distribution of price changes
        price_changes = np.diff(price_series) / price_series[:-1]
        p, bins = np.histogram(price_changes, bins="auto", density=True)

        # Calculate Shannon entropy
        randomShannonEntropy = entropy(p)

        # Calculate the probability distribution of price changes
        barsPriceChanges = (
            np.diff(self.bars.ClosePrices.data) / self.bars.ClosePrices.data[:-1]
        )
        barsP, bins = np.histogram(barsPriceChanges, bins="auto", density=True)

        # Calculate Shannon entropy
        barsShannonEntropy = entropy(barsP)
        """

        # self.chart = Chart(
        #     self.symbol,
        #     self.bars,
        #     self.bin_settings,
        # )

        self.time = self.initial_time = self.symbol.time
        pass

    def start(self):
        self.logger = PyLogger(self)
        header = (
            "\nNumber"
            + ",net_profit"
            + ",Balance"
            + ",Symbol"
            + ",Mode"
            + ",Volume"
            # + ",Swap"
            + ",OpenDate"
            + ",OpenTime"
            + ",CloseDate"
            + ",CloseTime"
            + ",OpenPrice"
            + ",ClosePrice"
            + ",TradeMargin"
            # + ",MaxEquityDrawdown"
        )

        self.log_mode = self.logger.SELF_MADE
        self.open_logfile(
            self.logger, self.version.split(" ")[0] + ".csv", self.log_mode, header
        )
        self.log_flush()

        self.max_equity[0] = self.Account.balance
        self.max_equity_drawdown_value[0] = 0

        self.loaded_robot.on_start(
            self, self.trade_direction in [TradeDirection.Mode1, TradeDirection.Long]
        )

        self.on_start()

    def tick(self):
        # update quote, bars, Indicators
        # of 1st tick must update all bars and Indicators which have been inized in on_start()
        for symbol in self.symbol_list:
            error = symbol.on_tick()
            if "" != error or self.symbol_list[0].time > self.bin_settings.end_dt:
                return True

        self.time = self.symbol_list[0].time

        ########################################
        # Update Account
        if len(self.positions) >= 1:
            if Platforms.Mt5Live == self.bin_settings.platform:
                import MetaTrader5 as mt5

                account_info = mt5.account_info()
                self.Account.balance = account_info.balance
                self.Account.equity = account_info.equity
                self.Account.margin = account_info.margin
                self.Account.FreeMargin = account_info.margin_free
                self.Account.MarginLevel = account_info.margin_level
                self.Account.unrealized_net_profit = account_info.profit
            else:
                open_positions_profit = 0
                for x in self.positions:
                    open_positions_profit += (
                        (x.current_price - x.entry_price)
                        * (1 if x.trade_type == TradeType.Buy else -1)
                        * x.volume_in_units
                    )
                    self.Account.unrealized_net_profit += open_positions_profit
                    x.max_drawdown = min(x.max_drawdown, open_positions_profit)

                self.Account.equity = self.Account.balance + open_positions_profit
            pass

        # check spread
        is_spread = True
        if (
            self.symbol.spread < 0
            or self.symbol.spread
            > 2 * self.market_values.avg_spread * self.symbol.tick_size
        ):
            is_spread = False
        self.is_trading_allowed = is_spread

        # call bot's on_tick
        self.loaded_robot.on_tick(self)

        # do max/min calcs
        self.max(self.max_margin, self.Account.margin)
        if self.max(self.same_time_open, len(self.positions)):
            self.same_time_open_date_time = self.time
            self.same_time_open_count = len(self.history)

        self.max(self.max_balance, self.Account.balance)
        if self.max(
            self.max_balance_drawdown_value, self.max_balance[0] - self.Account.balance
        ):
            self.max_balance_drawdown_time = self.time
            self.max_balance_drawdown_count = len(self.history)

        self.max(self.max_equity, self.Account.equity)
        if self.max(
            self.max_equity_drawdown_value, self.max_equity[0] - self.Account.equity
        ):
            self.max_equity_drawdown_time = self.time
            self.max_equity_drawdown_count = len(self.history)

        return False

    def stop(self):
        # call bot
        self.on_stop()

        # calc performance numbers
        min_duration = timedelta.max
        avg_duration_sum = 0
        max_duration = timedelta.min
        duration_count = 0
        max_invest_counter = [0] * 1
        # invest_count_histo = None
        avg_duration_sum += self.avg_open_duration_sum[0]
        duration_count += self.open_duration_count[0]
        min_duration = min(self.min_open_duration[0], min_duration)
        max_duration = max(self.max_open_duration[0], max_duration)
        self.loaded_robot.on_stop(self)
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
            + ConvertUtils.double_to_string(profit + loss, 2)
            + ",,,,Long: "
            + ConvertUtils.double_to_string(
                sum(
                    x.net_profit for x in self.history if x.trade_type == TradeType.Buy
                ),
                2,
            )
            + ",,,,Short:,"
            + ConvertUtils.double_to_string(
                sum(
                    x.net_profit for x in self.history if x.trade_type == TradeType.Sell
                ),
                2,
            )
        )

        # self.log_add_text_line("max_margin: " + self.Account.asset + " " + ConvertUtils.double_to_string(mMaxMargin, 2))
        # self.log_add_text_line("max_same_time_open: " + str(mSameTimeOpen)
        # + ", @ " + mSameTimeOpenDateTime.strftime("%d.%m.%Y %H:%M:%S")
        # + ", Count# " + str(mSameTimeOpenCount))
        self.log_add_text_line(
            "Max Balance Drawdown Value: "
            + self.Account.asset
            + " "
            + ConvertUtils.double_to_string(self.max_balance_drawdown_value[0], 2)
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
                else ConvertUtils.double_to_string(
                    100 * self.max_balance_drawdown_value[0] / self.max_balance[0], 2
                )
            )
        )

        self.log_add_text_line(
            "Max Equity Drawdown Value: "
            + self.Account.asset
            + " "
            + ConvertUtils.double_to_string(self.max_equity_drawdown_value[0], 2)
            + "; @ "
            + self.max_equity_drawdown_time.strftime("%d.%m.%Y %H:%M:%S")
            + "; Count# "
            + str(self.max_equity_drawdown_count)
        )

        self.log_add_text_line(
            "Max Current Equity Drawdown %: "
            + ConvertUtils.double_to_string(max_current_equity_dd_percent, 2)
        )

        self.log_add_text_line(
            "Max start Equity Drawdown %: "
            + ConvertUtils.double_to_string(max_start_equity_dd_percent, 2)
        )

        self.log_add_text_line(
            "Profit Factor: "
            + (
                "-"
                if loosing_trades == 0
                else ConvertUtils.double_to_string(profit_factor, 2)
            )
        )

        self.log_add_text_line(
            "Sharpe Ratio: " + ConvertUtils.double_to_string(sharpe_ratio, 2)
        )
        self.log_add_text_line(
            "Sortino Ratio: " + ConvertUtils.double_to_string(sortino_ratio, 2)
        )

        self.log_add_text_line(
            "Calmar Ratio: " + ConvertUtils.double_to_string(calmar, 2)
        )
        self.log_add_text_line(
            "Winning Ratio: " + ConvertUtils.double_to_string(winning_ratio_percent, 2)
        )

        self.log_add_text_line(
            "Trades Per Month: " + ConvertUtils.double_to_string(trades_per_month, 2)
        )

        self.log_add_text_line(
            "Average Annual Profit Percent: "
            + ConvertUtils.double_to_string(annual_profit_percent, 2)
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
        #         self.log_add_text_line("histo_rest_quotient: " + ConvertUtils.double_to_string(m_histo_rest_quotient = investCountHisto[1] / histoRestSum,
        self.log_close()

    def calculate_reward(self) -> float:
        return self.loaded_robot.get_tick_fitness(algo_api)

    # endregion


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

    def __init__(self, symbol: Symbol, is_long: bool, label: str):
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
            self.main_position = self.bot.execute_market_order(  # type: ignore
                TradeType.Buy if self.is_long else TradeType.Sell,
                self.symbol.name,
                self.symbol.normalize_volume_in_units(volume),
                self.label + label_ext,
            )

            if self.main_position is not None:  # type: ignore
                pass
                self.main_margin_after_open = self.bot.Account.margin
                self.freeze_price_offset = inherited_freeze_price_offset
                self.freeze_corrected_entry_price = self.main_position.entry_price

        return self.main_position is not None  # type: ignore

    def do_modify_volume(self, volume: float, current_open_price: float) -> bool:
        self.last_modified_time = self.bot.time
        self.freeze_corrected_entry_price = current_open_price
        if self.main_position is not None:  # type: ignore
            return self.main_position.modify_volume(volume).is_successful
        return False

        self.open_duration_count = [0] * 1  # arrays because of by reference
        self.min_open_duration = [timedelta.max] * 1
        self.avg_open_duration_sum = [timedelta.min] * 1
        self.max_open_duration = [timedelta.min] * 1

    def do_main_close(
        self,
        min_open_duration: list[timedelta],
        avg_open_duration_sum: list[timedelta],
        open_duration_count: list[int],
        max_open_duration: list[timedelta],
        is_utc: bool = True,
    ):
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