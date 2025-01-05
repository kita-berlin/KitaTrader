class MovingAverage(IIndicator, ABC):
    result: DataSeries = DataSeries()
    pass

