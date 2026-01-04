from abc import ABC
from Api.IIndicator import IIndicator
from Api.DataSeries import DataSeries


class MovingAverage(IIndicator):
    """
    Base class for Moving Average indicators.
    Provides common structure for all moving average indicators.
    """
    def __init__(self, source: DataSeries, periods: int):
        """
        Initialize a Moving Average indicator.
        
        Args:
            source: Source DataSeries
            periods: Number of periods
        """
        self.source: DataSeries = source
        self.periods: int = periods
        
        # Create result DataSeries as indicator result (ring buffer mode)
        # Size = periods (for ring buffer mode)
        self.result: DataSeries = DataSeries(source._parent, periods, is_indicator_result=True)
        self.result.set_owner_indicator(self)
        
        # Register this indicator with the source
        source.register_indicator(self)
