from abc import ABC
from Api.IIndicator import IIndicator
from Api.DataSeries import DataSeries


class MovingAverage(IIndicator, ABC):
    result: DataSeries

    def __init__(
        self,
        source: DataSeries,
        periods: int = 20,
    ):
        self.source: DataSeries = source
        self.periods: int = periods
        self.result = DataSeries(self.source.parent)

    pass


# end of file
