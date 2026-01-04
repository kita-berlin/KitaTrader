from Api.IIndicator import IIndicator
from Api.DataSeries import DataSeries
from Indicators.MovingAverage import MovingAverage


class WeightedMovingAverage(MovingAverage, IIndicator):
    def __init__(self, source: DataSeries, periods: int = 14, shift: int = 0):
        # Call parent constructor to initialize result DataSeries
        super().__init__(source, periods)
        self.shift: int = shift
        self._weight: int = 0

    def initialize(self) -> None:
        """1:1 port from C# WeightedMovingAverageIndicator.Initialize()"""
        # _weight = Enumerable.Range(1, Periods).Sum();
        self._weight = sum(range(1, self.periods + 1))

    def calculate(self, index: int) -> None:
        """
        1:1 port from C# WeightedMovingAverageIndicator.Calculate(int index)
        """
        # checked { ... }
        num = 0.0
        num2 = index
        
        # for (int num3 = Periods; num3 > 0; num3--)
        for num3 in range(self.periods, 0, -1):
            # num += (double)num3 * Source[num2];
            num += float(num3) * self.source[num2]
            num2 -= 1
        
        # Result[index + Shift] = num / (double)_weight;
        self.result[index + self.shift] = num / float(self._weight)
