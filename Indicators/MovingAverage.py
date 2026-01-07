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
        
        # Determine timeframe from source parent (for warm-up calculation)
        self.timeframe_seconds = source._parent.timeframe_seconds if hasattr(source, '_parent') else 0
        self.indicator_name = self.__class__.__name__
        
        # Create result DataSeries as indicator result (ring buffer mode)
        buf_size = max(periods, 2000)
        self.result: DataSeries = DataSeries(source._parent, buf_size, is_indicator_result=True)
        self.result.set_owner_indicator(self)
        
        # Register this indicator with the source
        source.register_indicator(self)
        
        # Recursion protection
        self._calculating_index = -1
    
    def lazy_calculate(self, index: int) -> None:
        """
        Triggered by DataSeries.__getitem__ to ensure value is calculated.
        """
        if index < 0:
            return

        # If already calculating this EXACT index (recursion), skip
        # But allow calculating previous indices (needed for recursive indicators like EMA)
        if self._calculating_index != -1 and index == self._calculating_index:
            return
            
        # If already calculated for this index, skip (simple caching)
        # CRITICAL: For non-full buffers, we need to check both _add_count and _last_calc_index
        # _add_count tells us if the value exists in the buffer
        # _last_calc_index tells us if it was actually calculated (not just a gap-filler NaN)
        if hasattr(self.result, '_last_calc_index') and self.result._last_calc_index >= index:
            # Value was calculated - check if it's a closed bar (doesn't need recalculation)
            # CRITICAL: Use source's _add_count - 1 to determine current bar, not count
            # count is capped at buffer size, while _add_count is the total number of bars ever added
            # For non-full buffers: count == _add_count, so both work
            # For full buffers: count == size (capped), but _add_count continues to grow
            # The current bar is at index = source._add_count - 1
            source_current_bar_idx = self.source._add_count - 1
            if index < source_current_bar_idx:
                return # Closed bar, already done
            # For current bar, we might need to recalculate on every tick
        
        # Set flag to prevent recursion
        old_calc_index = self._calculating_index
        self._calculating_index = index
        try:
            # Recursive indicators need iterative calculation of missing history
            last_calc = getattr(self.result, '_last_calc_index', -1)
            if last_calc < index - 1 and self.indicator_name in ["ExponentialMovingAverage", "HullMovingAverage"]:
                for i in range(last_calc + 1, index + 1):
                    self.calculate(i)
            else:
                self.calculate(index)
        finally:
            self._calculating_index = old_calc_index
    
    def initialize(self) -> None:
        pass
