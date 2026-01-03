from Api.IIndicator import IIndicator
from Api.DataSeries import DataSeries
from Indicators.MovingAverage import MovingAverage
import numpy as np
import math


class SimpleMovingAverage(MovingAverage, IIndicator):
    def __init__(self, source: DataSeries, periods: int = 14, shift: int = 0):
        # Call parent constructor to initialize result DataSeries
        super().__init__(source, periods)
        self.shift: int = shift
        self._digits: int = 5  # Default to 5 digits (forex standard)

        self.initialize()
        pass

    def _get_symbol_digits(self) -> int:
        """Get symbol digits from the parent bars"""
        try:
            # Access symbol through: source._parent._symbol.digits
            bars = self.source._parent
            if hasattr(bars, '_symbol') and bars._symbol:
                return bars._symbol.digits
        except:
            pass
        return self._digits  # Return default if unable to access

    def initialize(self) -> None:
        pass

    def calculate(self, index: int) -> None:
        # Bounds checking - use parent count, not data length (ring buffer size)
        if index < 0 or index >= self.source._parent.count:
            return
        
        index1 = index + self.shift
        if index1 < 0:
            return
        
        # Use double precision (float64) for all calculations - matching C# double precision exactly
        # C# code: double num = 0.0; for (int i = index - Periods + 1; i <= index; i++) { num += Source[i]; }
        # C# code: Result[index2] = num / (double)Periods;
        # C# does NOT round during calculation - pure double precision throughout
        # IMPORTANT: Use [] indexing exactly like C# - DataSeries.__getitem__() handles ring buffer mapping
        num = 0.0  # Python float is already 64-bit (double precision)
        index2 = index - self.periods + 1
        count = 0
        while index2 <= index:
            if index2 >= 0:
                # Use [] indexing exactly like C#: Source[index2]
                # DataSeries.__getitem__() maps absolute index to ring buffer position using _add_count
                val = self.source[index2]  # Use [] indexing - ring buffer mapping is transparent
                if not math.isnan(val):
                    # Convert to float (double precision) - NO rounding during accumulation (matching C# exactly)
                    val_float = float(val)  # Ensure double precision
                    num += val_float  # Accumulate in double precision (no rounding)
                    count += 1
            index2 += 1
        
        if count > 0:
            # Calculate average in double precision (matching C#: num / (double)Periods)
            # Note: C# uses Periods, but we use count (which may be less if some values are NaN)
            # NO rounding - store pure double precision value (matching C# exactly)
            result = num / float(count)
            # Write result using [] indexing - DataSeries.__getitem__() will map index correctly
            # For indicator results, we use write_indicator_value() which handles _add_count
            self.result.write_indicator_value(float(result))
            # Also store at result[index] for direct access (matching C# Result[index])
            # Note: write_indicator_value() already handles the ring buffer write, but we also
            # need to support result[index] access, which __getitem__() handles via _add_count
        else:
            # No valid values found - this should not happen if source has data
            pass