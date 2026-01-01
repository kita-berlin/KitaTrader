from Api.IIndicator import IIndicator
from Api.DataSeries import DataSeries
from Indicators.SimpleMovingAverage import SimpleMovingAverage
from Indicators.StandardDeviation import StandardDeviation
from Indicators.Vidya import Vidya
from Api.KitaApiEnums import *
import numpy as np


class BollingerBands(IIndicator):
    main: DataSeries
    top: DataSeries
    bottom: DataSeries

    def __init__(
        self,
        source: DataSeries,
        periods: int = 20,
        standard_deviations: float = 2.0,
        ma_type: MovingAverageType = MovingAverageType.Simple,
        shift: int = 0,
    ):
        self.source: DataSeries = source
        self.periods: int = periods
        self.standard_deviations: float = standard_deviations
        self.ma_type: MovingAverageType = ma_type
        self.shift: int = shift
        # DataSeries requires both parent and size
        # Get size from parent Bars (default to 1000 if not available)
        parent_bars = self.source._parent if hasattr(self.source, '_parent') else self.source.parent
        size = getattr(parent_bars, 'size', 1000) if hasattr(parent_bars, 'size') else 1000
        self.main = DataSeries(parent_bars, size)
        self.top = DataSeries(parent_bars, size)
        self.bottom = DataSeries(parent_bars, size)

        self.MovingAverage = None
        self.StandardDeviation = None

        self.initialize()
        pass

    def initialize(self):
        if self.ma_type == MovingAverageType.Vidya:
            self.MovingAverage = Vidya(self.source, self.periods)
        else:
            self.MovingAverage = SimpleMovingAverage(self.source, self.periods)
            
        self.StandardDeviation = StandardDeviation(self.source, self.periods, self.ma_type)

    def calculate(self, index: int) -> None:
        count = len(self.source.data)
        if count == 0 or index < 0:
            return
        
        # PERFORMANCE OPTIMIZATION: Only calculate the specific index requested
        # In cTrader, Calculate(index) is called for each new bar, so we only need to calculate that one index
        # However, we need to ensure all previous bars are calculated first
        if index < self.periods - 1:
            return  # Need at least 'periods' data points
        
        # Calculate sub-indicators for this specific index only
        self.MovingAverage.calculate(index)
        self.StandardDeviation.calculate(index)
        
        index1 = index + self.shift
        if index1 >= count or index1 < 0:
            return

        # Get the MA and StdDev values using the DataSeries accessor (handles circular buffer)
        ma_value = self.MovingAverage.result[index]  # type: ignore
        std_value = self.StandardDeviation.result[index]  # type: ignore
        
        import math
        if math.isnan(ma_value) or math.isnan(std_value):
            return  # Sub-indicators not calculated yet
        
        num = std_value * self.standard_deviations
        
        # cTrader pattern: IndicatorDataSeries is a simple list, write directly by index
        # Result[index] = value (or Result[index + Shift] = value)
        # Ensure the arrays are large enough (like cTrader's IndicatorDataSeriesAdapter does)
        # IMPORTANT: Resize BEFORE writing, not after bounds check
        while index1 >= len(self.main.data):
            # Extend arrays with NaN (matching cTrader's behavior)
            old_size = len(self.main.data)
            new_size = max(old_size * 2, index1 + 1)
            self.main.data = np.resize(self.main.data, new_size)
            self.top.data = np.resize(self.top.data, new_size)
            self.bottom.data = np.resize(self.bottom.data, new_size)
            # Fill new positions with NaN
            self.main.data[old_size:] = np.nan
            self.top.data[old_size:] = np.nan
            self.bottom.data[old_size:] = np.nan
        
        # Write directly to index (matching cTrader's simple assignment)
        self.main.data[index1] = ma_value
        self.bottom.data[index1] = ma_value - num
        self.top.data[index1] = ma_value + num


# end of file
