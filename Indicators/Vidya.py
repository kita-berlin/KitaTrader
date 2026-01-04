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

        
        prev_result = self.result[index - 1] if index > 0 else float('nan')
        
        # If previous result is NaN (start of calculation), use previous price
        import math
        if math.isnan(prev_result) or prev_result == 0:
            if index > 0:
                
                prev_result = self.source[index - 1]
            else:
                prev_result = self.source[index] if index >= 0 else float('nan')

        # Calculate CMO
        cmo_val = self.cmo(index)
        
        # Alpha = Sigma * CMO
        alpha = self.sigma * cmo_val
        
        
        current_price = self.source[index]
        
        
        # Result = (1 - alpha) * PrevResult + alpha * Price
        # Ensure all values are double precision and calculate without rounding
        result_value = (1.0 - float(alpha)) * float(prev_result) + float(alpha) * float(current_price)
        
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

            
            curr_price = float(self.source[curr_idx])  # Ensure double precision
            prev_price = float(self.source[prev_idx])  # Ensure double precision
            
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
