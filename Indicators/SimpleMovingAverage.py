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

        self.initialize()
        pass

    def initialize(self) -> None:
        pass

    def calculate(self, index: int) -> None:
        # Bounds checking
        if index < 0 or index >= len(self.source.data):
            return
        
        index1 = index + self.shift
        if index1 < 0:
            return
        
        num = 0.0
        index2 = index - self.periods + 1
        count = 0
        while index2 <= index:
            if index2 >= 0 and index2 < len(self.source.data):
                val = self.source[index2]
                if not math.isnan(val):
                    num += val
                    count += 1
            index2 += 1
        
        if count > 0:
            # cTrader pattern: IndicatorDataSeries grows as needed, write directly by index
            # Ensure array is large enough (like cTrader's IndicatorDataSeriesAdapter)
            # IMPORTANT: Resize BEFORE writing, not after bounds check
            while index1 >= len(self.result.data):
                old_size = len(self.result.data)
                new_size = max(old_size * 2, index1 + 1)
                self.result.data = np.resize(self.result.data, new_size)
                self.result.data[old_size:] = np.nan
            
            # Write directly to index (matching cTrader: Result[index2] = num / Periods)
            self.result.data[index1] = num / count
