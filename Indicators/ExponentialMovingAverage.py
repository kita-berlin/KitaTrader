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
        
        # Get parent for result DataSeries
        parent_bars = self.source._parent if hasattr(self.source, '_parent') else self.source.parent
        
        # For indicator results, use ring buffer with size exactly matching the period
        self.result = DataSeries(parent_bars, self.periods, is_indicator_result=True)
    
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
        
        # Get previous EMA value using last() method (works with ring buffers)
        prev_ema = self.result.last(1) if self.result._write_index > 0 else float('nan')
        
        # Get current source value using last() method
        source_count = self.source._parent.count
        if index < 0 or index >= source_count:
            return
        source_last_index = source_count - 1 - index
        current_value = self.source.last(source_last_index)
        
        import math
        if math.isnan(current_value):
            return
        
        # C# code: if (double.IsNaN(num2)) { Result[num] = Source[index]; }
        # C# code: else { Result[num] = Source[index] * _alpha + num2 * (1.0 - _alpha); }
        # C# uses pure double precision - NO rounding during calculation
        # Calculate EMA in pure double precision
        if math.isnan(prev_ema):
            # First value: EMA = Price (matching C#: Result[num] = Source[index])
            ema_value = float(current_value)  # Ensure double precision
        else:
            # EMA = Price * alpha + PrevEMA * (1 - alpha) (matching C# exactly)
            ema_value = float(current_value) * float(self._alpha) + float(prev_ema) * (1.0 - float(self._alpha))
        
        # Write to ring buffer - NO rounding, pure double precision (matching C# exactly)
        self.result.write_indicator_value(float(ema_value))
    


# end of file
