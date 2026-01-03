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
    
    def register_indicator(self, indicator) -> None:
        """
        Register an indicator with this DataSeries and update max period requirement.
        """
        if indicator not in self.indicator_list:
            self.indicator_list.append(indicator)
            # Update max period requirement if indicator has periods
            if hasattr(indicator, 'periods'):
                self._parent.update_max_period_requirement(indicator.periods)

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
        Supports both sequential and ring buffer modes.
        
        For indicator results (ring buffer mode):
        - last(0) = most recently written value
        - last(1) = previous value
        - Uses ringbuffer relative indexing (0 = most recent)
        """
        if index < 0:
            return float("nan")
        
        if self._is_indicator_result:
            # Indicator result ring buffer mode: use ringbuffer relative indexing
            # ringbuffer[0] = most recent, ringbuffer[1] = second most recent, etc.
            if self.data._count == 0:
                return float("nan")
            
            if index >= self.data._count:
                return float("nan")
            
            value = self.data[index]  # Ringbuffer[0] is most recent
            if value is None:
                return float("nan")
            return float(value) if not np.isnan(value) else float('nan')
        else:
            # Source DataSeries mode: uses parent Bars' count
            if index >= self._parent.count:
                return float("nan")
            
            # Use ringbuffer relative indexing
            # Map absolute index to relative position
            if self._parent.count <= self._size:
                # Sequential mode (buffer not full yet)
                # last(0) = most recent = ringbuffer[0]
                # last(1) = previous = ringbuffer[1]
                if index >= self.data._count:
                    return float("nan")
                value = self.data[index]
            else:
                # Ring buffer is full - use circular indexing
                # Map to relative position
                if index >= self.data._count:
                    return float("nan")
                value = self.data[index]
            
            if value is None:
                return float("nan")
            return float(value) if not np.isnan(value) else float('nan')
    
    def write_indicator_value(self, value: float) -> None:
        """
        Write a value to the indicator result ring buffer.
        Simply appends a new value to the data series ringbuffer.
        
        IMPORTANT: cTrader rounds the final indicator result with symbol.digits before storing.
        This matches the behavior where indicator values are rounded to symbol precision.
        """
        if not self._is_indicator_result:
            raise ValueError("write_indicator_value() can only be called on indicator result DataSeries")
        
        # Round the final result with symbol.digits (matching cTrader behavior)
        # This is the last step before returning calculated values to users
        digits = self._get_symbol_digits()
        rounded_value = round(value, digits)
        
        # Simply append to the ringbuffer
        self.data.add(rounded_value)
        self._add_count += 1
    
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
        Access value at absolute index using [] operator (matching C# Source[index]).
        Maps absolute index to ring buffer position using _add_count.
        
        This allows indicators to use source[index] exactly like C# uses Source[index],
        with the ring buffer implementation transparently handling the mapping.
        
        Args:
            index: Absolute index (0, 1, 2, ...) - linear count from first value added
            
        Returns:
            Value at the specified absolute index, or NaN if index is out of range
        """
        if index < 0:
            return float("nan")
        
        if self._is_indicator_result:
            # Indicator result ring buffer mode: size = period
            # Map absolute index to ring buffer relative position
            # Ringbuffer uses relative indexing: [0] = most recent, [1] = second most recent, etc.
            # Absolute index i maps to relative position (_add_count - 1 - i)
            if index >= self._add_count:
                return float("nan")  # Index beyond what we've added
            
            # Check if value still exists (hasn't been overwritten)
            if self._add_count > self._size:
                # Buffer full - check if value was overwritten
                if index < self._add_count - self._size:
                    return float("nan")  # Value was overwritten
            
            # Map absolute index to relative position
            # Absolute index 0 = oldest = relative position (_add_count - 1)
            # Absolute index (_add_count - 1) = newest = relative position 0
            rel_pos = self._add_count - 1 - index
            
            if rel_pos < 0 or rel_pos >= self.data._count:
                return float("nan")
            
            value = self.data[rel_pos]
            if value is None:
                return float("nan")
            return float(value) if not np.isnan(value) else float('nan')
        else:
            # Source DataSeries mode: uses parent Bars' count
            if index >= self._parent.count:
                return float("nan")
            
            # Map absolute index to ring buffer relative position
            if self._parent.count <= self._size:
                # Buffer not full yet - sequential access
                # Absolute index i maps to relative position (count - 1 - i)
                rel_pos = self._parent.count - 1 - index
                if rel_pos < 0 or rel_pos >= self.data._count:
                    return float("nan")
                value = self.data[rel_pos]
            else:
                # Buffer full - circular access
                # Values at indices < (count - size) have been overwritten
                if index < self._parent.count - self._size:
                    return float("nan")  # Value was overwritten
                # Map absolute index to relative position
                # Absolute index (count - size) = oldest = relative position (size - 1)
                # Absolute index (count - 1) = newest = relative position 0
                rel_pos = self._parent.count - 1 - index
                if rel_pos < 0 or rel_pos >= self.data._count:
                    return float("nan")
                value = self.data[rel_pos]
            
            if value is None:
                return float("nan")
            return float(value) if not np.isnan(value) else float('nan')


# end of file
