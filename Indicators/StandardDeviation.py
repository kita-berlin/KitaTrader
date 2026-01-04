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
        
        num2: float = self._movingAverage.result[index]
        
        # Loop through periods (matching cTrader: for (int i = 0; i < Periods; i++))
        
        
        
        
        for i in range(self.periods):
            src_idx = index - i
            if src_idx < 0:
                break
            
            source_val = float(self.source[src_idx])  # Ensure double precision
            if math.isnan(source_val):
                break
            diff = source_val - num2
            num1 += diff * diff  # Use multiplication instead of **2 for exact match with Math.Pow

        
        
        std_dev = math.sqrt(num1 / float(self.periods))
        # For indicator ring buffers, use write_indicator_value() which handles circular indexing
        self.result.write_indicator_value(float(std_dev))


# end of file
