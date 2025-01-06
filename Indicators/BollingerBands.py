from Api.IIndicator import IIndicator
from Api.DataSeries import DataSeries
from Indicators.SimpleMovingAverage import SimpleMovingAverage
from Indicators.StandardDeviation import StandardDeviation
from Api.KitaApiEnums import *


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
        self.main = DataSeries(self.source.parent)
        self.top = DataSeries(self.source.parent)
        self.bottom = DataSeries(self.source.parent)

        self.MovingAverage = None
        self.StandardDeviation = None

        self.initialize()
        pass

    def initialize(self):
        self.MovingAverage = SimpleMovingAverage(self.source, self.periods)
        self.StandardDeviation = StandardDeviation(self.source, self.periods)

    def calculate(self, index: int) -> None:
        count = len(self.source.data)
        for index in range(count):
            index1 = index + self.shift
            if index1 >= count or index1 < 0:
                continue

            num = self.StandardDeviation.result.data[index] * self.standard_deviations  # type: ignore
            self.main[index1] = self.MovingAverage.result.data[index]  # type: ignore
            self.bottom[index1] = self.MovingAverage.result.data[index] - num  # type: ignore
            self.top[index1] = self.MovingAverage.result.data[index] + num  # type: ignore


# end of file
