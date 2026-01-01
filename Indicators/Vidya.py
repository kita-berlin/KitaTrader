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

        # Ensure previous result exists
        prev_result = self.result[index - 1]
        
        # If previous result is NaN (start of calculation), use previous price
        import math
        if math.isnan(prev_result) or prev_result == 0:
            if index > 0:
                prev_result = self.source[index - 1]
            else:
                prev_result = self.source[index]

        # Calculate CMO
        cmo_val = self.cmo(index)
        
        # Alpha = Sigma * CMO
        alpha = self.sigma * cmo_val
        
        # Result = (1 - alpha) * PrevResult + alpha * Price
        self.result.data[index] = (1.0 - alpha) * prev_result + alpha * self.source[index]

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

            curr_price = self.source[curr_idx]
            prev_price = self.source[prev_idx]
            
            import math
            if math.isnan(curr_price) or math.isnan(prev_price):
                continue
                
            diff = curr_price - prev_price
            if diff > 0.0:
                num += diff
            else:
                num2 += abs(diff)

        if num + num2 == 0.0:
            return 0.0
            
        return abs((num - num2) / (num + num2))
