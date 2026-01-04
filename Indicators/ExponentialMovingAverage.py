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
        # checked { int num = index + Shift; ... }
        num = index + self.shift
        num2 = self.result[num - 1]
        
        # if (double.IsNaN(num2))
        if math.isnan(num2):
            # Result[num] = Source[index];
            self.result[num] = self.source[index]
        else:
            # Result[num] = Source[index] * _alpha + num2 * (1.0 - _alpha);
            self.result[num] = self.source[index] * self._alpha + num2 * (1.0 - self._alpha)
