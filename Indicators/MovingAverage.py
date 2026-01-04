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
        # Get parent for result DataSeries
        parent_bars = self.source._parent if hasattr(self.source, '_parent') else self.source.parent
        
        # For indicator results, use ring buffer with size exactly matching the period
        # This saves memory and ensures we only keep the necessary data
        self.result = DataSeries(parent_bars, self.periods, is_indicator_result=True)
        self.result.set_owner_indicator(self)

    pass


# end of file
