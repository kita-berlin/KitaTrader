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
        # Size = periods (for true ring buffer mode)
        # But for backtesting, we might want a larger buffer if we access old values.
        # For OHLCTest, we only access Last(1), so 'periods' is enough.
        # However, to be safe and match cTrader's long history, we use a larger default or dynamic resizing.
        # For now, let's use 2000 or parent count if available.
        buf_size = max(periods, 2000)
        self.result: DataSeries = DataSeries(source._parent, buf_size, is_indicator_result=True)
        self.result.set_owner_indicator(self)
        
        # Register this indicator with the source
        source.register_indicator(self)
    
    def lazy_calculate(self, index: int) -> None:
        """
        Triggered by DataSeries.__getitem__ to ensure value is calculated.
        """
        if index < self.periods - 1:
            return
            
        # If already calculated for this index, skip (simple caching)
        if hasattr(self.result, '_last_calc_index') and self.result._last_calc_index == index:
            # But wait! For the "current" bar, we might need to recalculate on every tick
            if index < self.source._parent.count - 1:
                return # Closed bar, already done
        
        self.calculate(index)
    
    def initialize(self) -> None:
        pass
