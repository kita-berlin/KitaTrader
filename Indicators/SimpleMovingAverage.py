from Api.IIndicator import IIndicator
from Api.DataSeries import DataSeries
from Indicators.MovingAverage import MovingAverage


class SimpleMovingAverage(MovingAverage, IIndicator):
    def __init__(self, source: DataSeries, periods: int = 14, shift: int = 0):
        # Call parent constructor to initialize result DataSeries
        super().__init__(source, periods)
        self.shift: int = shift

    def initialize(self) -> None:
        """Required by IIndicator interface (empty in C# version)"""
        pass

    def calculate(self, index: int) -> None:
        """
        1:1 port from C# SimpleMovingAverageIndicator.Calculate(int index)
        """
        index2 = index + self.shift
        num = 0.0
        for i in range(index - self.periods + 1, index + 1):
            num += self.source[i]
        
        # Result[index2] = num / (double)Periods;
        self.result[index2] = num / float(self.periods)
