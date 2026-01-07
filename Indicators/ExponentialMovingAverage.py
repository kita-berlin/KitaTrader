from Api.IIndicator import IIndicator
from Api.DataSeries import DataSeries
from Indicators.MovingAverage import MovingAverage
import math


class ExponentialMovingAverage(MovingAverage, IIndicator):
    def __init__(self, source: DataSeries, periods: int = 14, shift: int = 0):
        # Call parent constructor to initialize result DataSeries
        super().__init__(source, periods)
        self.shift: int = shift
        self._alpha: float = 0.0

    def initialize(self) -> None:
        """1:1 port from C# ExponentialMovingAverageIndicator.Initialize()"""
        # _alpha = 2.0 / (double)checked(Periods + 1);
        self._alpha = 2.0 / float(self.periods + 1)

    def calculate(self, index: int) -> None:
        """
        1:1 port from C# ExponentialMovingAverageIndicator.Calculate(int index)
        """
        # Verify index is valid for source DataSeries (timeframe-independent check)
        if index < 0 or index >= self.source._add_count:
            # Use the newest available index
            index = self.source._add_count - 1
            if index < 0:
                return
        
        # checked { int num = index + Shift; ... }
        num = index + self.shift
        
        # CRITICAL: For recursive indicators like EMA, we need to ensure previous values are calculated
        # Before accessing result[num - 1], trigger lazy calculation if needed
        # This ensures that when the buffer is NOT full and indicators are calculated out of order,
        # we still have the correct previous value
        # NOTE: We trigger lazy calculation here, but __getitem__ will also trigger it
        # The lazy_calculate method has recursion protection, so it's safe to call twice
        if num > 0:
            prev_index = num - 1
            # Check if previous value needs to be calculated
            # CRITICAL: When buffer is NOT full, result._add_count might be < source._add_count
            # So we need to check if prev_index is beyond what's been calculated
            if prev_index >= self.result._add_count:
                # Previous index hasn't been calculated yet - trigger lazy calculation
                # But only if we're not already calculating that exact index (to avoid recursion)
                if self._calculating_index != prev_index:
                    self.lazy_calculate(prev_index)
        
        # Read the previous value
        prev_index = num - 1
        num2 = self.result[prev_index]
        
        # if (double.IsNaN(num2))
        if math.isnan(num2):
            # Result[num] = Source[index];
            source_val = self.source[index]
            self.result[num] = source_val
        else:
            # Result[num] = Source[index] * _alpha + num2 * (1.0 - _alpha);
            source_val = self.source[index]
            result_val = source_val * self._alpha + num2 * (1.0 - self._alpha)
            self.result[num] = result_val
