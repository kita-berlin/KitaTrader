from abc import ABC
from Api.IIndicator import IIndicator
from Api.DataSeries import DataSeries


class StandardIndicator(ABC, IIndicator):
    """
    Base class for standard indicators (non-MovingAverage indicators).
    Provides common structure for indicators that don't inherit from MovingAverage.
    """
    def __init__(self, source: DataSeries, periods: int = None):
        """
        Initialize a Standard Indicator.
        
        Args:
            source: Source DataSeries
            periods: Number of periods (optional, some indicators don't use periods)
        """
        self.source: DataSeries = source
        self.periods: int = periods
        
        # Create result DataSeries as indicator result (ring buffer mode)
        # For standard indicators, use periods if available, otherwise use a default size
        result_size = periods if periods is not None else source._parent.count if hasattr(source, '_parent') else 1000
        self.result: DataSeries = DataSeries(source._parent, result_size, is_indicator_result=True)
        self.result.set_owner_indicator(self)
        
        # Register this indicator with the source
        source.register_indicator(self)
    
    def create_data_series(self) -> DataSeries:
        """
        Create an internal DataSeries for indicator calculations.
        1:1 port of C# CreateDataSeries() method.
        """
        # Create a DataSeries with the same size as the parent
        size = self.source._parent.count if hasattr(self.source, '_parent') else 1000
        return DataSeries(self.source._parent, size, is_indicator_result=False)
