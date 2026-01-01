"""
Moving Average Convergence Divergence (MACD) CrossOver Indicator
Ported from cTrader.Automate.Indicators
"""
from Api.IIndicator import IIndicator
from Api.DataSeries import DataSeries
from Indicators.ExponentialMovingAverage import ExponentialMovingAverage


class MacdCrossOver(IIndicator):
    """
    Moving Average Convergence Divergence (MACD) CrossOver
    
    The MACD is a trend-following momentum indicator that shows the relationship 
    between two moving averages of prices.
    
    Formula:
        MACD Line = EMA(source, fast_periods) - EMA(source, slow_periods)
        Signal Line = EMA(MACD Line, signal_periods)
    """
    
    def __init__(
        self,
        source: DataSeries,
        long_cycle: int = 26,
        short_cycle: int = 12,
        signal_periods: int = 9
    ):
        """
        Initialize MACD CrossOver
        
        Args:
            source: Input data series (typically close prices)
            long_cycle: Number of periods for the slow EMA (default: 26)
            short_cycle: Number of periods for the fast EMA (default: 12)
            signal_periods: Number of periods for the signal Line EMA (default: 9)
        """
        self.source: DataSeries = source
        self.long_cycle: int = long_cycle
        self.short_cycle: int = short_cycle
        self.signal_periods: int = signal_periods
        
        # Get parent and size for DataSeries
        parent_bars = self.source._parent if hasattr(self.source, '_parent') else self.source.parent
        size = getattr(parent_bars, 'size', 1000) if hasattr(parent_bars, 'size') else 1000
        
        # Create internal DataSeries for MACD line
        self.macd = DataSeries(parent_bars, size)
        
        # Create result DataSeries (Signal line)
        self.signal = DataSeries(parent_bars, size)
        
        # Create EMAs for fast and slow cycles
        self._ema_fast = ExponentialMovingAverage(self.source, short_cycle)
        self._ema_slow = ExponentialMovingAverage(self.source, long_cycle)
        
        # Create EMA for signal line (based on MACD line)
        self._ema_signal = ExponentialMovingAverage(self.macd, signal_periods)
        
    def initialize(self) -> None:
        """Initialize the indicator"""
        pass
        
    def calculate(self, index: int) -> None:
        """
        Calculate MACD for the given index
        
        Args:
            index: The bar index to calculate
        """
        # Calculate fast and slow EMAs
        self._ema_fast.calculate(index)
        self._ema_slow.calculate(index)
        
        # Get EMA values
        fast_val = self._ema_fast.result.data[index]
        slow_val = self._ema_slow.result.data[index]
        
        import math
        if fast_val is None or slow_val is None or math.isnan(fast_val) or math.isnan(slow_val):
            return
            
        # MACD Line = Fast EMA - Slow EMA
        self.macd.data[index] = fast_val - slow_val
        
        # Calculate Signal Line (EMA of MACD Line)
        self._ema_signal.calculate(index)
        
        # Get Signal Line value
        signal_val = self._ema_signal.result.data[index]
        if signal_val is not None:
            self.signal.data[index] = signal_val

# end of file
