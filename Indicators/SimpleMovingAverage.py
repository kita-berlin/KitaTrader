from Api.IIndicator import IIndicator
from Api.DataSeries import DataSeries
from Indicators.MovingAverage import MovingAverage


class SimpleMovingAverage(MovingAverage, IIndicator):
    def __init__(self, source: DataSeries, periods: int = 14, shift: int = 0):
        self.source: DataSeries = source
        self.periods: int = periods
        self.shift: int = shift

        self.initialize()
        pass

    def initialize(self) -> None:
        pass

    def calculate(self, index: int) -> None:
        index1 = index + self.shift
        num = 0.0
        index2 = index - self.periods + 1
        while index2 <= index:
            num += self.source[index2]
            index2 += 1
        self.result[index1] = num / self.periods


# end of file
