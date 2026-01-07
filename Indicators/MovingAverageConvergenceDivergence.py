from Api.IIndicator import IIndicator
from Api.DataSeries import DataSeries
from Indicators.StandardIndicator import StandardIndicator
import math


class MovingAverageConvergenceDivergence(StandardIndicator, IIndicator):
    """
    Moving Average Convergence Divergence (MACD) indicator.
    1:1 port from cTrader.
    """
    def __init__(self, source: DataSeries, fast_periods: int = 12, slow_periods: int = 26, signal_periods: int = 9):
        # slow_periods is the primary period for size initialization
        super().__init__(source, slow_periods) 
        self.fast_periods = fast_periods
        self.slow_periods = slow_periods
        self.signal_periods = signal_periods
        
        # MACD has 3 outputs. All must be indicator results to allow writing values.
        self.macd = self.result
        self.signal = self.create_data_series(is_indicator_result=True)
        self.histogram = self.create_data_series(is_indicator_result=True)
        
        # Internal indicators
        self._fast_ema = None
        self._slow_ema = None
        self._signal_ema = None

    def initialize(self) -> None:
        from Indicators.ExponentialMovingAverage import ExponentialMovingAverage
        
        self._fast_ema = ExponentialMovingAverage(self.source, self.fast_periods)
        self._fast_ema.initialize()
        
        self._slow_ema = ExponentialMovingAverage(self.source, self.slow_periods)
        self._slow_ema.initialize()
        
        # Signal Line is an EMA of the MACD line itself
        self._signal_ema = ExponentialMovingAverage(self.macd, self.signal_periods)
        self._signal_ema.initialize()

    def calculate(self, index: int) -> None:
        """
        1:1 port from cTrader MACD.Calculate(int index)
        """
        fast_val = self._fast_ema.result[index]
        slow_val = self._slow_ema.result[index]
        
        if math.isnan(fast_val) or math.isnan(slow_val):
            self.macd[index] = float('nan')
            self.signal[index] = float('nan')
            self.histogram[index] = float('nan')
            return
            
        # C# MacdCrossOver uses: _emaShort - _emaLong
        # When called as MacdCrossOver(source, 12, 26, 9):
        #   Parameter order is: (source, longCycle, shortCycle, signalPeriods)
        #   So: longCycle=12, shortCycle=26
        #   _emaLong = EMA(LongCycle) = EMA(12), _emaShort = EMA(ShortCycle) = EMA(26)
        #   MACD = _emaShort - _emaLong = EMA(26) - EMA(12)
        # But Python macd(source, 12, 26, 9) means: fast=12, slow=26
        # So to match C#, we need: slow - fast = EMA(26) - EMA(12)
        macd_line = slow_val - fast_val
        # Normalize very small values near zero to 0.0 to match C# behavior
        if abs(macd_line) < 1e-6:  # Less than 0.000001, effectively zero for 5-digit precision
            macd_line = 0.0
        self.macd[index] = macd_line
        
        # Accessing signal_ema.result[index] will trigger calculation for MACD Line's EMA
        signal_val = self._signal_ema.result[index]
        
        if math.isnan(signal_val):
            self.signal[index] = float('nan')
            self.histogram[index] = float('nan')
            return
            
        self.signal[index] = signal_val
        self.histogram[index] = macd_line - signal_val
