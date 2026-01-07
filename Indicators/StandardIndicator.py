from abc import ABC, abstractmethod
from Api.IIndicator import IIndicator
from Api.DataSeries import DataSeries


class StandardIndicator(IIndicator, ABC):
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
        
        # Determine timeframe from source parent (for warm-up calculation)
        self.timeframe_seconds = source._parent.timeframe_seconds if hasattr(source, '_parent') else 0
        self.indicator_name = self.__class__.__name__
        
        # Create result DataSeries as indicator result (ring buffer mode)
        buf_size = max(periods if periods is not None else 0, 2000)
        self.result: DataSeries = DataSeries(source._parent, buf_size, is_indicator_result=True)
        self.result.set_owner_indicator(self)
        
        # Register this indicator with the source
        source.register_indicator(self)
        
        # Recursion protection
        self._calculating_index = -1
    
    def lazy_calculate(self, index: int) -> None:
        """
        Triggered by DataSeries.__getitem__ to ensure value is calculated.
        Matches MovingAverage logic.
        """
        if index < 0:
            return

        # If already calculating this index (recursion), skip
        if self._calculating_index != -1 and index <= self._calculating_index:
            return
            
        # If already calculated for this index, skip (simple caching)
        if hasattr(self.result, '_last_calc_index') and self.result._last_calc_index >= index:
            if index < self.source._parent.count - 1:
                return # Closed bar, already done
        
        # Set flag to prevent recursion
        old_calc_index = self._calculating_index
        self._calculating_index = index
        try:
            # Recursive indicators like RSI/MACD need iterative calculation
            last_calc = getattr(self.result, '_last_calc_index', -1)
            if last_calc < index - 1 and self.indicator_name in ["RelativeStrengthIndex", "MovingAverageConvergenceDivergence"]:
                for i in range(last_calc + 1, index + 1):
                    self.calculate(i)
            else:
                self.calculate(index)
        finally:
            self._calculating_index = old_calc_index

    def initialize(self) -> None:
        """Default implementation of initialize"""
        pass

    @abstractmethod
    def calculate(self, index: int) -> None:
        """Subclasses must implement calculate"""
        pass

    def create_data_series(self, is_indicator_result: bool = False) -> DataSeries:
        """
        Create an internal DataSeries for indicator calculations.
        1:1 port of C# CreateDataSeries() method.
        """
        count = self.source._parent.count if hasattr(self.source, '_parent') else 1000
        size = max(count, 2000)
        ds = DataSeries(self.source._parent, size, is_indicator_result=is_indicator_result)
        if is_indicator_result:
            ds.set_owner_indicator(self)
        return ds
