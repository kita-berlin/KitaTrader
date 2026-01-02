from abc import ABC
from Api.IIndicator import IIndicator
from Api.DataSeries import DataSeries
from Indicators.MovingAverage import MovingAverage
import math


class Vidya(MovingAverage):
    def __init__(
        self,
        source: DataSeries,
        periods: int = 14,
        sigma: float = 0.65,
    ):
        super().__init__(source, periods)
        self.sigma: float = sigma
        self.initialize()
        pass

    def initialize(self):
        # Nothing special to initialize
        pass

    def calculate(self, index: int) -> None:
        if index < self.periods:
            return

        # Get previous result using last(1) (ring buffer mode)
        # last(1) gives the value written before the most recent one
        source_count = self.source._parent.count
        prev_result = self.result.last(1) if self.result._write_index > 0 else float('nan')
        
        # If previous result is NaN (start of calculation), use previous price
        import math
        if math.isnan(prev_result) or prev_result == 0:
            if index > 0 and index - 1 < source_count:
                source_last_index = source_count - 1 - (index - 1)
                prev_result = self.source.last(source_last_index)
            elif index < source_count:
                source_last_index = source_count - 1 - index
                prev_result = self.source.last(source_last_index)

        # Calculate CMO
        cmo_val = self.cmo(index)
        
        # Alpha = Sigma * CMO
        alpha = self.sigma * cmo_val
        
        # Get current price using last()
        if index < source_count:
            source_last_index = source_count - 1 - index
            current_price = self.source.last(source_last_index)
        else:
            current_price = float('nan')
        
        # C# uses pure double precision - NO rounding during calculation
        # Result = (1 - alpha) * PrevResult + alpha * Price
        # Ensure all values are double precision and calculate without rounding
        result_value = (1.0 - float(alpha)) * float(prev_result) + float(alpha) * float(current_price)
        # Write to ring buffer - NO rounding, pure double precision (matching C# exactly)
        self.result.write_indicator_value(float(result_value))

    def cmo(self, index: int) -> float:
        num = 0.0
        num2 = 0.0
        
        for i in range(self.periods):
            # Calculate difference: Price[last] - Price[last-1]
            # In cTrader: Price[index - i] - Price[index - i - 1]
            
            # Check bounds
            curr_idx = index - i
            prev_idx = index - i - 1
            if prev_idx < 0:
                continue

            # Convert absolute indices to last() indices: [idx] = last(count - 1 - idx)
            source_count = self.source._parent.count
            if curr_idx < source_count:
                curr_last_index = source_count - 1 - curr_idx
                curr_price = float(self.source.last(curr_last_index))  # Ensure double precision
            else:
                curr_price = float('nan')
            if prev_idx < source_count:
                prev_last_index = source_count - 1 - prev_idx
                prev_price = float(self.source.last(prev_last_index))  # Ensure double precision
            else:
                prev_price = float('nan')
            
            import math
            if math.isnan(curr_price) or math.isnan(prev_price):
                continue
                
            # Calculate difference in pure double precision (no rounding)
            diff = curr_price - prev_price
            if diff > 0.0:
                num += diff  # Accumulate positive differences
            else:
                num2 += abs(diff)  # Accumulate absolute value of negative differences

        if num + num2 == 0.0:
            return 0.0
            
        return abs((num - num2) / (num + num2))
