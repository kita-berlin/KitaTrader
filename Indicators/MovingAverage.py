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
        # DataSeries requires both parent and size
        parent_bars = self.source._parent if hasattr(self.source, '_parent') else self.source.parent
        size = getattr(parent_bars, 'size', 1000) if hasattr(parent_bars, 'size') else 1000
        self.result = DataSeries(parent_bars, size)

    pass


# end of file
