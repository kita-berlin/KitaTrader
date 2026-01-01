"""
Exponential Moving Average (EMA) Indicator
Ported from cTrader.Automate.Indicators
"""
from Api.IIndicator import IIndicator
from Api.DataSeries import DataSeries


class ExponentialMovingAverage(IIndicator):
    """
    Exponential Moving Average (EMA)
    
    The EMA gives more weight to recent prices, making it more responsive to new information
    than a Simple Moving Average.
    
    Formula:
        EMA(t) = Price(t) * alpha + EMA(t-1) * (1 - alpha)
        where alpha = 2 / (periods + 1)
        
    For the first calculation (when previous EMA is NaN), EMA = Price
    """
    
    def __init__(
        self,
        source: DataSeries,
        periods: int = 14,
        shift: int = 0
    ):
        """
        Initialize Exponential Moving Average
        
        Args:
            source: Input data series (typically close prices)
            periods: Number of periods for EMA calculation (default: 14)
            shift: Shift the indicator forward/backward (default: 0)
        """
        self.source: DataSeries = source
        self.periods: int = periods
        self.shift: int = shift
        
        # Calculate alpha (smoothing factor)
        self._alpha: float = 2.0 / (periods + 1)
        
        # Get parent and size for result DataSeries
        parent_bars = self.source._parent if hasattr(self.source, '_parent') else self.source.parent
        size = getattr(parent_bars, 'size', 1000) if hasattr(parent_bars, 'size') else 1000
        
        # Create result DataSeries
        self.result = DataSeries(parent_bars, size)
    
    def initialize(self) -> None:
        """Initialize the indicator (required by IIndicator interface)"""
        # Alpha is already calculated in __init__
        pass
        
    def calculate(self, index: int) -> None:
        """
        Calculate EMA for the given index
        
        Args:
            index: The bar index to calculate
        """
        count = len(self.source.data)
        if count == 0 or index < 0:
            return
            
        # Apply shift
        shifted_index = index + self.shift
        if shifted_index >= count or shifted_index < 0 or shifted_index >= len(self.result.data):
            return
        
        # Get previous EMA value
        if shifted_index > 0:
            prev_ema = self.result.data[shifted_index - 1]
        else:
            prev_ema = None
        
        # Get current source value
        current_value = self.source.data[index]
        if current_value is None:
            return
        
        # Calculate EMA
        import math
        if prev_ema is None or math.isnan(prev_ema):
            # First value: EMA = Price
            self.result.data[shifted_index] = current_value
        else:
            # EMA = Price * alpha + PrevEMA * (1 - alpha)
            self.result.data[shifted_index] = current_value * self._alpha + prev_ema * (1.0 - self._alpha)
    
    def __getitem__(self, index: int) -> float:
        """Allow array-style access to results"""
        return self.result[index]


# end of file
