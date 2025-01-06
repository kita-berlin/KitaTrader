import math
from Api.IIndicator import IIndicator
from Api.DataSeries import DataSeries
from Api.KitaApiEnums import *
from Indicators.MovingAverage import MovingAverage
from Indicators.SimpleMovingAverage import SimpleMovingAverage


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
        self.result = DataSeries(self.source.parent)
        self.initialize()
        pass

    def initialize(self):
        self._movingAverage: MovingAverage = SimpleMovingAverage(self.source, self.periods)

    def calculate(self, index: int) -> None:
        num1: float = 0.0
        num2: float = self._movingAverage.result[index]
        num3: int = 0
        while num3 < self.periods:
            if index - num3 < 0:
                break
            num1 += (self.source[index - num3] - num2) ** 2
            num3 += 1

        self.result[index] = math.sqrt(num1 / self.periods)


# end of file
