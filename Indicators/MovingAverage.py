from abc import ABC
from Api.IIndicator import IIndicator
from Api.DataSeries import DataSeries


class MovingAverage(IIndicator, ABC):
    result: DataSeries = DataSeries()
    pass


# end of file
