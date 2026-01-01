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
        # DataSeries requires both parent and size
        parent_bars = self.source._parent if hasattr(self.source, '_parent') else self.source.parent
        size = getattr(parent_bars, 'size', 1000) if hasattr(parent_bars, 'size') else 1000
        self.result = DataSeries(parent_bars, size)
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
            if src_idx < 0 or src_idx >= len(self.source.data):
                break
            num1 += (self.source[src_idx] - num2) ** 2

        # cTrader pattern: IndicatorDataSeries grows as needed, write directly by index
        # Ensure array is large enough (like cTrader's IndicatorDataSeriesAdapter)
        # IMPORTANT: Resize BEFORE writing, not after bounds check
        while index >= len(self.result.data):
            old_size = len(self.result.data)
            new_size = max(old_size * 2, index + 1)
            self.result.data = np.resize(self.result.data, new_size)
            self.result.data[old_size:] = np.nan
        
        # Write directly to index (matching cTrader: Result[index] = sqrt(num1 / Periods))
        self.result.data[index] = math.sqrt(num1 / self.periods)


# end of file
