from Api.IIndicator import IIndicator
from Api.DataSeries import DataSeries
from Indicators.StandardIndicator import StandardIndicator
import math


class StandardDeviation(StandardIndicator, IIndicator):
    """
    Standard Deviation indicator.
    1:1 port from cTrader.
    """
    def __init__(self, source: DataSeries, periods: int = 14):
        super().__init__(source, periods)

    def calculate(self, index: int) -> None:
        """
        1:1 port from cTrader StandardDeviation.Calculate(int index)
        """
        if index < self.periods - 1:
            self.result[index] = float('nan')
            return
            
        # Calc Mean
        sum_val = 0.0
        for i in range(self.periods):
            sum_val += self.source[index - i]
        
        mean = sum_val / self.periods
        
        # Calc variance
        sum_sq_diff = 0.0
        for i in range(self.periods):
            diff = self.source[index - i] - mean
            sum_sq_diff += diff * diff
            
        variance = sum_sq_diff / self.periods
        self.result[index] = math.sqrt(variance)
