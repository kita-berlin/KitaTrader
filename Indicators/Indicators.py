from Api.DataSeries import DataSeries
from Indicators.MovingAverage import MovingAverage
from Indicators.SimpleMovingAverage import SimpleMovingAverage
from Indicators.ExponentialMovingAverage import ExponentialMovingAverage
from Indicators.RelativeStrengthIndex import RelativeStrengthIndex
from Indicators.Vidya import Vidya
from Indicators.MacdCrossOver import MacdCrossOver
from Indicators.MacdHistogram import MacdHistogram
from Indicators.BollingerBands import BollingerBands
from Indicators.StandardDeviation import StandardDeviation
from Api.KitaApiEnums import *
from typing import List, Tuple, Optional


class IndicatorInfo:
    """Information about a created indicator for warm-up calculation"""
    def __init__(self, indicator, periods: int, timeframe_seconds: int, indicator_name: str):
        self.indicator = indicator
        self.periods = periods
        self.timeframe_seconds = timeframe_seconds
        self.indicator_name = indicator_name


class Indicators:
    """
    Central API for creating indicators, similar to cTrader's mBot.Indicators.
    Tracks all created indicators for automatic warm-up calculation.
    """
    def __init__(self, api=None):
        """
        Initialize the Indicators accessor.
        
        Args:
            api: Optional KitaApi instance to track indicators for warm-up calculation
        """
        self.api = api
        self._created_indicators: List[IndicatorInfo] = []  # Track all created indicators
    
    def _register_indicator(self, indicator, periods: int, timeframe_seconds: int, indicator_name: str):
        """Register an indicator for warm-up calculation"""
        if self.api is not None:
            # Get timeframe from the source DataSeries's parent Bars
            if hasattr(indicator, 'source') and hasattr(indicator.source, '_parent'):
                bars = indicator.source._parent
                if hasattr(bars, 'timeframe_seconds'):
                    timeframe_seconds = bars.timeframe_seconds
            
            info = IndicatorInfo(indicator, periods, timeframe_seconds, indicator_name)
            self._created_indicators.append(info)
    
    def get_warmup_periods(self) -> List[Tuple[int, int, str]]:
        """
        Get all warm-up periods from registered indicators.
        Returns list of (periods, timeframe_seconds, indicator_name) tuples.
        """
        result = []
        for info in self._created_indicators:
            result.append((info.periods, info.timeframe_seconds, info.indicator_name))
        return result

    def moving_average(
        self,
        source: DataSeries,
        periods: int = 14,
        ma_type: MovingAverageType = MovingAverageType.Simple,
    ) -> tuple[str, MovingAverage]:
        if MovingAverageType.Simple == ma_type:
            indicator = SimpleMovingAverage(source, periods)
            # Register indicator and update max period requirement
            if hasattr(source, 'register_indicator'):
                source.register_indicator(indicator)
            else:
                source.indicator_list.append(indicator)
            # Get timeframe from source's parent Bars
            timeframe_seconds = 0
            if hasattr(source, '_parent') and hasattr(source._parent, 'timeframe_seconds'):
                timeframe_seconds = source._parent.timeframe_seconds
            self._register_indicator(indicator, periods, timeframe_seconds, "SimpleMovingAverage")
            return "", indicator
        elif MovingAverageType.Exponential == ma_type:
            indicator = ExponentialMovingAverage(source, periods)
            # Register indicator and update max period requirement
            if hasattr(source, 'register_indicator'):
                source.register_indicator(indicator)
            else:
                source.indicator_list.append(indicator)
            timeframe_seconds = 0
            if hasattr(source, '_parent') and hasattr(source._parent, 'timeframe_seconds'):
                timeframe_seconds = source._parent.timeframe_seconds
            self._register_indicator(indicator, periods, timeframe_seconds, "ExponentialMovingAverage")
            return "", indicator
        # Add other MA types as they are implemented
        return None  # type: ignore

    def exponential_moving_average(
        self,
        source: DataSeries,
        periods: int = 14,
    ) -> tuple[str, ExponentialMovingAverage]:
        indicator = ExponentialMovingAverage(source, periods)
        # Register indicator and update max period requirement
        if hasattr(source, 'register_indicator'):
            source.register_indicator(indicator)
        else:
            source.indicator_list.append(indicator)
        timeframe_seconds = 0
        if hasattr(source, '_parent') and hasattr(source._parent, 'timeframe_seconds'):
            timeframe_seconds = source._parent.timeframe_seconds
        self._register_indicator(indicator, periods, timeframe_seconds, "ExponentialMovingAverage")
        return "", indicator

    def relative_strength_index(
        self,
        source: DataSeries,
        periods: int = 14,
    ) -> tuple[str, RelativeStrengthIndex]:
        indicator = RelativeStrengthIndex(source, periods)
        # Register indicator and update max period requirement
        if hasattr(source, 'register_indicator'):
            source.register_indicator(indicator)
        else:
            source.indicator_list.append(indicator)
        timeframe_seconds = 0
        if hasattr(source, '_parent') and hasattr(source._parent, 'timeframe_seconds'):
            timeframe_seconds = source._parent.timeframe_seconds
        # RSI uses EMA with period 2*periods-1, which is longer
        effective_periods = 2 * periods - 1
        self._register_indicator(indicator, effective_periods, timeframe_seconds, "RelativeStrengthIndex")
        return "", indicator

    def vidya(
        self,
        source: DataSeries,
        periods: int = 14,
        sigma: float = 0.65,
    ) -> tuple[str, Vidya]:
        indicator = Vidya(source, periods, sigma)
        # Register indicator and update max period requirement
        if hasattr(source, 'register_indicator'):
            source.register_indicator(indicator)
        else:
            source.indicator_list.append(indicator)
        timeframe_seconds = 0
        if hasattr(source, '_parent') and hasattr(source._parent, 'timeframe_seconds'):
            timeframe_seconds = source._parent.timeframe_seconds
        self._register_indicator(indicator, periods, timeframe_seconds, "Vidya")
        return "", indicator

    def macd_cross_over(
        self,
        source: DataSeries,
        long_cycle: int = 26,
        short_cycle: int = 12,
        signal_periods: int = 9,
    ) -> tuple[str, MacdCrossOver]:
        indicator = MacdCrossOver(source, long_cycle, short_cycle, signal_periods)
        # Register indicator and update max period requirement
        if hasattr(source, 'register_indicator'):
            source.register_indicator(indicator)
        else:
            source.indicator_list.append(indicator)
        timeframe_seconds = 0
        if hasattr(source, '_parent') and hasattr(source._parent, 'timeframe_seconds'):
            timeframe_seconds = source._parent.timeframe_seconds
        # MACD uses long_cycle as the longest period
        self._register_indicator(indicator, long_cycle, timeframe_seconds, "MacdCrossOver")
        return "", indicator

    def macd_histogram(
        self,
        source: DataSeries,
        long_cycle: int = 26,
        short_cycle: int = 12,
        signal_periods: int = 9,
    ) -> tuple[str, MacdHistogram]:
        indicator = MacdHistogram(source, long_cycle, short_cycle, signal_periods)
        # Register indicator and update max period requirement
        if hasattr(source, 'register_indicator'):
            source.register_indicator(indicator)
        else:
            source.indicator_list.append(indicator)
        timeframe_seconds = 0
        if hasattr(source, '_parent') and hasattr(source._parent, 'timeframe_seconds'):
            timeframe_seconds = source._parent.timeframe_seconds
        # MACD uses long_cycle as the longest period
        self._register_indicator(indicator, long_cycle, timeframe_seconds, "MacdHistogram")
        return "", indicator

    def standard_deviation(
        self,
        source: DataSeries,
        periods: int = 14,
        ma_type: MovingAverageType = MovingAverageType.Simple,
    ) -> tuple[str, StandardDeviation]:
        indicator = StandardDeviation(source, periods, ma_type)
        # Register indicator and update max period requirement
        if hasattr(source, 'register_indicator'):
            source.register_indicator(indicator)
        else:
            source.indicator_list.append(indicator)
        timeframe_seconds = 0
        if hasattr(source, '_parent') and hasattr(source._parent, 'timeframe_seconds'):
            timeframe_seconds = source._parent.timeframe_seconds
        self._register_indicator(indicator, periods, timeframe_seconds, "StandardDeviation")
        return "", indicator

    def bollinger_bands(
        self,
        source: DataSeries,
        periods: int = 20,
        standard_deviations: float = 2.0,
        ma_type: MovingAverageType = MovingAverageType.Simple,
        shift: int = 0,
    ) -> tuple[str, BollingerBands]:
        indicator = BollingerBands(source, periods, standard_deviations, ma_type, shift)
        # Register indicator and update max period requirement
        if hasattr(source, 'register_indicator'):
            source.register_indicator(indicator)
        else:
            source.indicator_list.append(indicator)
        timeframe_seconds = 0
        if hasattr(source, '_parent') and hasattr(source._parent, 'timeframe_seconds'):
            timeframe_seconds = source._parent.timeframe_seconds
        # Bollinger Bands uses the periods parameter
        self._register_indicator(indicator, periods, timeframe_seconds, "BollingerBands")
        return "", indicator

# end of file
