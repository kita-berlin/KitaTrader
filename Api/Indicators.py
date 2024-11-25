import numpy as np
import pandas as pd
from abc import ABC, abstractmethod
from CoFu import *
from DataSeries import DataSeries
from Bars import Bars


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


class moving_average(IIndicator, ABC):
    Result: DataSeries = DataSeries()
    pass


class simple_moving_average(moving_average, IIndicator):
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
        self.Result[index1] = num / self.periods


class standard_deviation(IIndicator):
    Result: DataSeries = DataSeries()

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

    def initialize(self) -> None:
        self._movingAverage: moving_average = Indicators.moving_average(
            self.source, self.periods, self.ma_type
        )

    def calculate(self, index: int) -> None:
        num1: float = 0.0
        num2: float = self._movingAverage.Result[index]
        num3: int = 0
        while num3 < self.periods:
            if index - num3 < 0:
                break
            num1 += (self.source[index - num3] - num2) ** 2
            num3 += 1

        self.Result[index] = np.sqrt(num1 / self.periods)


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

        self.moving_average = None
        self.standard_deviation = None

        self.initialize()
        pass

    def initialize(self):
        self.moving_average = Indicators.moving_average(
            self.source, self.periods, self.ma_type
        )
        self.standard_deviation = Indicators.standard_deviation(
            self.source, self.periods
        )

    def calculate(self, index: int) -> None:
        for index in range(self.source.count):
            index1 = index + self.shift
            if index1 >= self.source.count or index1 < 0:
                continue

            num = self.standard_deviation.Result.data[index] * self.standard_deviations
            self.Main[index1] = self.moving_average.Result.data[index]
            self.Bottom[index1] = self.moving_average.Result.data[index] - num
            self.Top[index1] = self.moving_average.Result.data[index] + num


class Indicators:
    indicator_list = []

    def __init__(self, tradingClass):
        self.trading_class = tradingClass
        pass

    def moving_average(
        self,
        source: DataSeries,
        periods: int = 14,
        ma_type: MovingAverageType = MovingAverageType.Simple,
    ) -> moving_average:
        if MovingAverageType.Simple == ma_type:
            indicator = simple_moving_average(source, periods)
            # if MovingAverageType...

            source.indicator_list.append(indicator)
            return indicator
        pass

    def standard_deviation(
        self,
        source: DataSeries,
        periods: int = 14,
        ma_type: MovingAverageType = MovingAverageType.Simple,
    ) -> standard_deviation:
        indicator = standard_deviation(source, periods, ma_type)
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
        indicator = BollingerBands(
            source, periods, standard_deviations, ma_type, shift
        )
        source.indicator_list.append(indicator)
        return indicator

    # Hide
    # region
    def exponential_moving_average(self, source: DataSeries, periods: int):
        # Exponential Moving Average indicator instance
        pass

    def weighted_moving_average(self, source: DataSeries, periods: int):
        # Weighted Moving Average indicator instance
        pass

    def simple_moving_average(self, source: DataSeries, periods: int):
        # Simple Moving Average indicator instance
        pass

    def triangular_moving_average(self, source: DataSeries, periods: int):
        # Triangular Moving Average indicator instance
        pass

    def high_minus_low(self, bars=None):
        # High Minus Low indicator instance with bars
        if None == bars:
            bars = self.trading_class.bars

        pass

    def true_range(self, bars):
        # True Range indicator instance with bars
        if None == bars:
            bars = self.trading_class.bars

        pass

    def welles_wilder_smoothing(self, source: DataSeries, periods: int):
        # Welles Wilder Smoothing indicator instance
        pass

    def hull_moving_average(self, source: DataSeries, periods: int):
        # Hull Moving Average indicator instance
        pass

    def swing_index(self, limitMoveValue, bars: Bars = None):
        # Swing Index indicator instance with bars
        pass

    def accumulative_swing_index(self, limitMoveValue, bars: Bars = None):
        # Accumulative Swing Index indicator instance with bars
        pass

    def aroon(self, bars: Bars, periods: int):
        # Aroon indicator instance with bars
        pass

    def relative_strength_index(self, source: DataSeries, periods: int):
        # Relative Strength Index indicator instance
        pass

    def time_series_moving_average(self, source: DataSeries, periods: int):
        # Time Series Moving Average indicator instance
        pass

    def linear_regression_forecast(self, source: DataSeries, periods: int):
        # Linear Regression Forecast indicator instance
        pass

    def linear_regression_r_squared(self, source: DataSeries, periods: int):
        # Linear Regression R-Squared indicator instance
        pass

    def price_roc(self, source: DataSeries, periods: int):
        # Price Rate of Change indicator instance
        pass

    def vidya(self, source: DataSeries, periods: int, r2Scale):
        # Vidya indicator instance
        pass

    def ultimate_oscillator(self, bars: Bars, cycle1: int, cycle2: int, cycle3: int):
        # Ultimate Oscillator indicator instance with bars
        pass

    def directional_movement_system(self, bars: Bars, periods: int):
        # Directional Movement System indicator instance with bars
        pass

    def parabolic_sar(self, bars: Bars, minAf: float, maxAf: float):
        # Parabolic SAR indicator instance with bars
        pass

    def stochastic_oscillator(self, bars: Bars, kPeriods, kSlowing, dPeriods, ma_type):
        # Stochastic Oscillator indicator instance with bars
        pass

    def momentum_oscillator(self, source: DataSeries, periods: int):
        # Momentum Oscillator indicator instance
        pass

    def median_price(self, bars):
        # Median Price indicator instance with bars
        if None == bars:
            bars = self.trading_class.bars

        pass

    def williams_accumulation_distribution(self, bars):
        # Williams Accumulation Distribution indicator instance with bars
        if None == bars:
            bars = self.trading_class.bars

        pass

    def fractal_chaos_bands(self, bars):
        # Fractal Chaos Bands indicator instance with bars
        if None == bars:
            bars = self.trading_class.bars

        pass

    def typical_price(self, bars):
        # Typical Price indicator instance with bars
        if None == bars:
            bars = self.trading_class.bars

        pass

    def commodity_channel_index(self, bars: Bars, periods: int):
        # Commodity Channel Index indicator instance with bars
        pass

    def historical_volatility(self, source: DataSeries, periods: int, barHistory):
        # Historical Volatility indicator instance
        pass

    def mass_index(self, bars: Bars, periods: int):
        # Mass Index indicator instance with bars
        pass

    def chaikin_volatility(self, bars: Bars, periods: int, rateOfChange, ma_type):
        # Chaikin Volatility indicator instance with bars
        pass

    def detrended_price_oscillator(self, source: DataSeries, periods: int, ma_type):
        # Detrended Price Oscillator indicator instance
        pass

    def linear_regression_intercept(self, source: DataSeries, periods: int):
        # Linear Regression Intercept indicator instance
        pass

    def linear_regression_slope(self, source: DataSeries, periods: int):
        # Linear Regression Slope indicator instance
        pass

    def macd_histogram(self, source: DataSeries, longCycle, shortCycle, signalPeriods):
        # MACD Histogram indicator instance with DataSeries source
        pass

    def macd_cross_over(
        self, source: DataSeries, longCycle, shortCycle, signalPeriods
    ):
        # MACD cross_over indicator instance with DataSeries source
        pass

    def price_oscillator(self, source: DataSeries, longCycle, shortCycle, ma_type):
        # Price Oscillator indicator instance
        pass

    def rainbow_oscillator(self, source: DataSeries, levels, ma_type):
        # Rainbow Oscillator indicator instance
        pass

    def vertical_horizontal_filter(self, source: DataSeries, periods: int):
        # Vertical Horizontal Filter indicator instance
        pass

    def williams_pct_r(self, bars: Bars, periods: int):
        # Williams Percent R indicator instance with bars
        pass

    def trix(self, source: DataSeries, periods: int):
        # Trix indicator instance
        pass

    def weighted_close(self, bars):
        # Weighted Close indicator instance with bars
        if None == bars:
            bars = self.trading_class.bars

        pass

    def chaikin_money_flow(self, bars: Bars, periods: int):
        # Chaikin Money Flow indicator instance with bars
        pass

    def ease_of_movement(self, periods: int, ma_type):
        # Ease Of Movement indicator instance
        bars = self.trading_class.bars

        pass

    def money_flow_index(self, bars: Bars, periods: int):
        # Money Flow Index indicator instance with bars
        pass

    def negative_volume_index(self, source):
        # Negative Volume Index indicator instance
        pass

    def on_balance_volume(self, source):
        # On Balance Volume indicator instance
        pass

    def positive_volume_index(self, source):
        # Positive Volume Index indicator instance
        pass

    def price_volume_trend(self, source):
        # Price Volume Trend indicator instance
        pass

    def trade_volume_index(self, source):
        # trade Volume Index indicator instance
        pass

    def volume_oscillator(self, bars: Bars, shortTerm, longTerm):
        # Volume Oscillator indicator instance with bars
        pass

    def volume_roc(self, bars: Bars, periods: int):
        # Volume Rate of Change indicator instance with bars
        pass

    def average_true_range(self, bars: Bars, periods: int, ma_type):
        # Average True Range indicator instance with bars
        pass

    def donchian_channel(self, periods: int):
        # Donchian Channel indicator instance
        pass

    # endregion