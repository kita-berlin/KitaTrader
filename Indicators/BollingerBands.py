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
        # For indicator results, use ring buffer with size exactly matching the period
        # This saves memory and ensures we only keep the necessary data
        parent_bars = self.source._parent if hasattr(self.source, '_parent') else self.source.parent
        self.main = DataSeries(parent_bars, self.periods, is_indicator_result=True)
        self.top = DataSeries(parent_bars, self.periods, is_indicator_result=True)
        self.bottom = DataSeries(parent_bars, self.periods, is_indicator_result=True)

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

        # Get the MA and StdDev values using [] indexing exactly like C#: Result[index]
        ma_value = self.MovingAverage.result[index]  # type: ignore
        std_value = self.StandardDeviation.result[index]  # type: ignore
        
        import math
        if math.isnan(ma_value) or math.isnan(std_value):
            return  # Sub-indicators not calculated yet
        
        # C# code: double num = _standardDeviation.Result[index] * StandardDeviations;
        # C# code: Main[index2] = _movingAverage.Result[index];
        # C# code: Bottom[index2] = _movingAverage.Result[index] - num;
        # C# code: Top[index2] = _movingAverage.Result[index] + num;
        # C# uses pure double precision - NO rounding during calculation
        num = float(std_value) * float(self.standard_deviations)  # Ensure double precision
        
        # For indicator ring buffers, use write_indicator_value() which handles circular indexing
        # The result is always written to the current position, regardless of index
        # NO rounding - store pure double precision values (matching C# exactly)
        self.main.write_indicator_value(float(ma_value))
        self.bottom.write_indicator_value(float(ma_value - num))
        self.top.write_indicator_value(float(ma_value + num))


# end of file
