import Api.DataSeries as DataSeries

class BollingerBands(IIndicator):
    Main: DataSeries = DataSeries()
    Top: DataSeries = DataSeries()
    Bottom: DataSeries = DataSeries()

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

        self.MovingAverage = None
        self.StandardDeviation = None

        self.initialize()
        pass

    def initialize(self):
        self.MovingAverage = SimpleMovingAverage(self.source, self.periods)
        self.StandardDeviation = StandardDeviation(self.source, self.periods)

    def calculate(self, index: int) -> None:
        for index in range(self.source.count):
            index1 = index + self.shift
            if index1 >= self.source.count or index1 < 0:
                continue

            num = self.StandardDeviation.result.data[index] * self.standard_deviations  # type: ignore
            self.Main[index1] = self.MovingAverage.result.data[index]  # type: ignore
            self.Bottom[index1] = self.MovingAverage.result.data[index] - num  # type: ignore
            self.Top[index1] = self.MovingAverage.result.data[index] + num  # type: ignore

