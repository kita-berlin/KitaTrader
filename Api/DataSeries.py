from __future__ import annotations
from typing import TYPE_CHECKING, Iterator, Any
import numpy as np
from typing import Iterator
from Api.ring_buffer import Ringbuffer

# from Api.IIndicator import IIndicator

if TYPE_CHECKING:
    from Api.Bars import Bars


class DataSeries:
    data: Ringbuffer[float]
    _parent: Bars
    _size: int
    _is_indicator_result: bool  # True if this is an indicator result (ring buffer mode)
    _add_count: int  # Total number of values added (linear count, for mapping absolute indices)

    def __init__(self, _parent: Bars, _size: int, is_indicator_result: bool = False):
        """
        Initialize a DataSeries with a ring buffer.
        
        Args:
            _parent: Parent Bars object
            _size: Size of the buffer. For indicator results, this should be exactly the indicator's period.
            is_indicator_result: If True, this DataSeries is an indicator result and uses ring buffer mode with size = period.
        """
        self._parent = _parent
        self._size = _size
        self._is_indicator_result = is_indicator_result
        self._add_count = 0  # Track total number of values added (linear count)
        self.data = Ringbuffer[float](_size)  # Use true ringbuffer
        self.indicator_list = []  # List of indicators attached to this DataSeries
        self._owner_indicator = None  # The indicator that produces this DataSeries as a result
        self._last_calc_index = -1  # Last absolute index calculated for this indicator result
    
    def register_indicator(self, indicator) -> None:
        """
        Register an indicator with this DataSeries and update max period requirement.
        """
        if indicator not in self.indicator_list:
            self.indicator_list.append(indicator)
            # Update max period requirement if indicator has periods
            if hasattr(indicator, 'periods'):
                self._parent.update_max_period_requirement(indicator.periods)

    def set_owner_indicator(self, indicator) -> None:
        """
        Set the indicator that owns/produces this DataSeries.
        """
        self._owner_indicator = indicator

    def resize(self, new_size: int) -> None:
        """
        Resize the underlying Ringbuffer while preserving existing data.
        """
        if new_size <= self._size:
            return
            
        old_buffer = self.data
        self._size = new_size
        self.data = Ringbuffer[float](new_size)
        
        # Copy data from old buffer (from oldest to newest)
        for i in range(old_buffer._count - 1, -1, -1):
            self.data.add(old_buffer[i])
        
        # _add_count remains the same (total added since start)

    def __iter__(self) -> Iterator[float]:
        """
        Iterate over the valid elements in the buffer.
        """
        # For Ringbuffer, iterate from oldest to newest
        count = min(self.data._count, self._parent.count if not self._is_indicator_result else self.data._count)
        for i in range(count):
            rel_pos = count - 1 - i  # Convert to relative position (0 = most recent)
            if rel_pos < self.data._count:
                value = self.data[rel_pos]
                if value is not None:
                    yield float(value) if not np.isnan(value) else float('nan')

    def append(self, value: float):
        """
        Append a single value to the ring buffer.
        Uses the ringbuffer's natural circular behavior (overwrites oldest when full).
        For tick data, this allows unbounded growth by using the ringbuffer's circular nature.
        """
        # Simply add to ringbuffer - it will overwrite oldest when full (circular behavior)
        self.data.add(value)
        self._add_count += 1
    
    def append_ring(self, value: float, position: int):
        """
        Append a value to a specific position in the ring buffer.
        Used for ring buffer mode where data overwrites oldest entries.
        Increments _add_count to track linear count of values added.
        """
        if position < 0 or position >= self._size:
            return  # Invalid position
        # For ringbuffer, we use add() which automatically handles circular indexing
        # If we need to set at a specific position, we need to use __setitem__
        # But append_ring is legacy - for new code, use add() directly
        self.data.add(value)
        self._add_count += 1  # Increment linear count

    def last(self, index: int) -> float:
        """
        Retrieve the last `index`-th element from the buffer.
        last(0) = current bar, last(1) = 1 bar ago, etc.
        
        Args:
            index: Number of elements back from the newest (0 = newest)
        """
        # For indicator results, trigger lazy calculation if requested and possible
        if index < 0 or index >= self._parent.count:
            return float("nan")
        
        # For indicator results, trigger lazy calculation if requested and possible
        if self._is_indicator_result and self._owner_indicator:
            # last(index) corresponds to absolute index: current_count - index
            abs_index = max(0, self._parent.count - 1 - index)
            if hasattr(self._owner_indicator, 'lazy_calculate'):
                self._owner_indicator.lazy_calculate(abs_index)
                
        if index < 0 or index >= self.data._count:
            return float("nan")
        
        # Ringbuffer[0] is the most recent (last added)
        value = self.data[index]
        if value is None:
            return float("nan")
        return float(value) if not np.isnan(value) else float('nan')
    
    def write_indicator_value(self, value: float) -> None:
        """
        Write a value to the indicator result ring buffer and advance _add_count.
        Equivalent to cTrader's logic when a value is appended to an IndicatorDataSeries.
        """
        if not self._is_indicator_result:
            raise ValueError("write_indicator_value() can only be called on indicator result DataSeries")
        
        
        digits = self._get_symbol_digits()
        rounded_value = round(value, digits) if not np.isnan(value) else float('nan')
        
        # Simply append to the ringbuffer
        self.data.add(rounded_value)
        self._add_count += 1
        self._last_calc_index = self._add_count - 1

    def exchange_indicator_value(self, value: float) -> None:
        """
        Replace the most recent indicator value (current bar, index 0).
        Used for updating indicators on every tick without advancing history.
        """
        if not self._is_indicator_result:
            raise ValueError("exchange_indicator_value() can only be called on indicator result DataSeries")
        
        # Round the final result
        digits = self._get_symbol_digits()
        rounded_value = round(value, digits) if not np.isnan(value) else float('nan')
        
        # Use Ringbuffer.exchange to overwrite the last element
        self.data.exchange(rounded_value)
        # Note: _add_count and _last_calc_index stay the same because we didn't advance
    
    def _get_symbol_digits(self) -> int:
        """Get symbol digits from the parent bars"""
        try:
            # Access symbol through: _parent._symbol.digits
            if hasattr(self._parent, '_symbol') and self._parent._symbol:
                return self._parent._symbol.digits
        except:
            pass
        return 5  # Default to 5 digits (forex standard) if unable to access

    def get_average(self) -> float:
        """
        Compute the average of the current data in the buffer.
        """
        if self.data._count == 0:
            return float("nan")
        values = [float(self.data[i]) for i in range(self.data._count) if self.data[i] is not None and not np.isnan(self.data[i])]
        if not values:
            return float("nan")
        return float(np.mean(values))

    def get_max(self) -> float:
        """
        Compute the maximum of the current data in the buffer.
        """
        if self.data._count == 0:
            return float("nan")
        values = [float(self.data[i]) for i in range(self.data._count) if self.data[i] is not None and not np.isnan(self.data[i])]
        if not values:
            return float("nan")
        return float(np.max(values))

    def get_min(self) -> float:
        """
        Compute the minimum of the current data in the buffer.
        """
        if self.data._count == 0:
            return float("nan")
        values = [float(self.data[i]) for i in range(self.data._count) if self.data[i] is not None and not np.isnan(self.data[i])]
        if not values:
            return float("nan")
        return float(np.min(values))

    def __getitem__(self, index: int) -> float:
        """
        Access value at absolute index i (0 = first value EVER added).
        Maps to ringbuffer relative position based on _add_count and current count.
        Returns NaN if the value was overwritten.
        """
        # For indicator results, trigger lazy calculation if requested and possible
        if self._is_indicator_result and self._owner_indicator:
            if hasattr(self._owner_indicator, 'lazy_calculate'):
                self._owner_indicator.lazy_calculate(index)

        if index < 0 or index >= self._add_count:
            return float("nan")
        
        # Check if value still exists (hasn't been overwritten)
        if self._add_count > self._size:
            if index < self._add_count - self._size:
                return float("nan")  # Value was overwritten
        
        # Absolute index i maps to relative position (rel_pos)
        rel_pos = (self._add_count - 1) - index
        
        if 0 <= rel_pos < self.data._count:
            value = self.data[rel_pos]
            if value is None:
                return float("nan")
            return float(value) if not np.isnan(value) else float('nan')
        
        return float("nan")

    def __setitem__(self, index: int, value: float):
        """
        Set value at absolute index i (matching C# Result[index] = value).
        If index == _add_count, it appends a new value.
        If index < _add_count, it updates an existing (non-overwritten) value.
        """
        if index < 0:
            return
            
        if index == self._add_count:
            # Append mode
            self.write_indicator_value(value)
        elif index < self._add_count:
            # Update mode
            if self._add_count > self._size:
                if index < self._add_count - self._size:
                    return # Value already overwritten in ringbuffer
            
            rel_pos = (self._add_count - 1) - index
            if 0 <= rel_pos < self.data._count:
                
                rounded_value = round(value, self._get_symbol_digits()) if not np.isnan(value) else float('nan')
                self.data[rel_pos] = rounded_value
        else:
            # index > _add_count: Gap! Fill with NaNs
            while self._add_count < index:
                self.write_indicator_value(float("nan"))
            self.write_indicator_value(value)

    def _get_nearest_index(self, timestamp: datetime) -> int:
        """
        Find the absolute index whose OpenTime is closest to timestamp (without exceeding it).
        Used for synchronizing indicators across timeframes.
        """
        # This only makes sense if the parent is Bars and has open_times
        if not hasattr(self._parent, 'open_times'):
            return -1
            
        open_times = self._parent.open_times
        count = self._parent.count
        # Start from most recent and go backwards
        for i in range(count - 1, -1, -1):
            t = open_times.last(count - 1 - i)
            if t <= timestamp:
                return i
        return -1


# end of file
