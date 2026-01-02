import math
import numpy as np
from Api.IIndicator import IIndicator
from Api.DataSeries import DataSeries
from Api.KitaApiEnums import *
from Indicators.MovingAverage import MovingAverage
from Indicators.SimpleMovingAverage import SimpleMovingAverage
from Indicators.Vidya import Vidya


class StandardDeviation(IIndicator):
    result: DataSeries

    def __init__(
        self,
        source: DataSeries,
        periods: int = 14,
        ma_type: MovingAverageType = MovingAverageType.Simple,
    ):
        self.source: DataSeries = source
        self.periods: int = periods
        self.ma_type: MovingAverageType = ma_type
        # Get parent for result DataSeries
        parent_bars = self.source._parent if hasattr(self.source, '_parent') else self.source.parent
        
        # For indicator results, use ring buffer with size exactly matching the period
        self.result = DataSeries(parent_bars, self.periods, is_indicator_result=True)
        self.initialize()
        pass

    def initialize(self):
        if self.ma_type == MovingAverageType.Vidya:
            self._movingAverage = Vidya(self.source, self.periods)
        else:
            self._movingAverage = SimpleMovingAverage(self.source, self.periods)

    def calculate(self, index: int) -> None:
        # Bounds checking - matching cTrader's StandardDeviationIndicator
        # Note: Don't check index >= len(self.result.data) here - we resize it below
        if index < 0 or index >= len(self.source.data):
            return
        
        # cTrader pattern: Calculate moving average for this index first (it will auto-calculate if needed)
        # In cTrader, accessing _movingAverage.Result[index] automatically triggers Calculate(index)
        # In our implementation, we need to explicitly call it
        self._movingAverage.calculate(index)
        
        # Calculate standard deviation for this specific index only (matching cTrader)
        num1: float = 0.0
        source_count = self.source._parent.count
        # Get the MA value using last(0) since it was just calculated for this index (ring buffer mode)
        num2: float = self._movingAverage.result.last(0)
        
        # Loop through periods (matching cTrader: for (int i = 0; i < Periods; i++))
        # C# code: for (int i = 0; i < Periods; i++) { num += Math.Pow(Source[index - i] - num2, 2.0); }
        # C# code: Result[index] = Math.Sqrt(num / (double)Periods);
        # C# uses pure double precision - NO rounding during calculation
        for i in range(self.periods):
            src_idx = index - i
            if src_idx < 0 or src_idx >= source_count:
                break
            # Convert absolute index to last() index: [src_idx] = last(count - 1 - src_idx)
            source_last_index = source_count - 1 - src_idx
            source_val = float(self.source.last(source_last_index))  # Ensure double precision
            diff = source_val - num2
            num1 += diff * diff  # Use multiplication instead of **2 for exact match with Math.Pow

        # Calculate standard deviation in pure double precision (matching C#: Math.Sqrt(num / (double)Periods))
        # NO rounding - store pure double precision value (matching C# exactly)
        std_dev = math.sqrt(num1 / float(self.periods))
        # For indicator ring buffers, use write_indicator_value() which handles circular indexing
        self.result.write_indicator_value(float(std_dev))


# end of file
