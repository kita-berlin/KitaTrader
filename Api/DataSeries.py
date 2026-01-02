from __future__ import annotations
from typing import TYPE_CHECKING, Iterator, Any
import numpy as np
import numpy as np
from typing import Iterator

# from Api.IIndicator import IIndicator

if TYPE_CHECKING:
    from Api.Bars import Bars


class DataSeries:
    data: np.ndarray[Any, np.dtype[np.float64]]
    _parent: Bars
    _size: int
    _is_indicator_result: bool  # True if this is an indicator result (ring buffer mode)
    _write_index: int  # Current write position for indicator ring buffers

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
        self._write_index = 0  # Start at position 0 for ring buffers
        self.data = np.full(self._size, np.nan)  # Pre-fill with NaN
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
        return iter(self.data[: self._parent.count])

    def append(self, value: float):
        """
        Append a single value to the buffer (legacy method - use append_ring for ring buffers).
        For ring buffers, use append_ring() instead.
        """
        # Legacy behavior: resize if full (for backward compatibility)
        if self._parent.count == self._size:
            # Double the _size of the buffer
            new_size = self._size * 2
            new_data = np.full(new_size, np.nan)

            part1 = self.data[self._parent.count :]  # From index to end of the buffer
            part2 = self.data[: self._parent.count]  # From start to index
            new_data[: self._size] = np.concatenate((part1, part2))

            self.data = new_data
            self._size = new_size

        self.data[self._parent.count] = value
    
    def append_ring(self, value: float, position: int):
        """
        Append a value to a specific position in the ring buffer.
        Used for ring buffer mode where data overwrites oldest entries.
        """
        if position < 0 or position >= self._size:
            return  # Invalid position
        self.data[position] = value

    def last(self, index: int) -> float:
        """
        Retrieve the last `index`-th element from the buffer.
        last(0) = current bar, last(1) = 1 bar ago, etc.
        Supports both sequential and ring buffer modes.
        
        For indicator results (ring buffer mode):
        - last(0) = most recently written value (at _write_index - 1)
        - last(1) = previous value (at _write_index - 2)
        - Uses circular indexing with size = period
        """
        if index < 0:
            return float("nan")
        
        if self._is_indicator_result:
            # Indicator result ring buffer mode: size = period, uses _write_index
            # _write_index points to the next write position
            # last(0) = value at (_write_index - 1) % size
            # last(1) = value at (_write_index - 2) % size
            if self._write_index == 0:
                # No values written yet
                return float("nan")
            
            size = self._size
            # Calculate position: (_write_index - 1 - index) % size
            pos = (self._write_index - 1 - index) % size
            if pos < 0:
                pos += size
            
            if pos < 0 or pos >= len(self.data):
                return float("nan")
            return self.data[pos]
        else:
            # Source DataSeries mode: uses parent Bars' count and read_index
            if index >= self._parent.count:
                return float("nan")
            
            # Ring buffer mode: read_index points to the newest bar
            size = self._size
            if self._parent.count >= size:
                # Ring buffer is full - use circular indexing
                # last(0) = current bar = read_index
                # last(1) = previous bar = (read_index - 1) % size
                pos = (self._parent.read_index - index) % size
            else:
                # Sequential mode (buffer not full yet)
                # last(0) = current bar = count - 1
                # last(1) = previous bar = count - 2
                pos = self._parent.count - 1 - index
            
            if pos < 0 or pos >= len(self.data):
                return float("nan")
            return self.data[pos]
    
    def write_indicator_value(self, value: float) -> None:
        """
        Write a value to the indicator result ring buffer.
        For indicator results, this writes to the current _write_index position and advances it.
        
        IMPORTANT: cTrader rounds the final indicator result with symbol.digits before storing.
        This matches the behavior where indicator values are rounded to symbol precision.
        """
        if not self._is_indicator_result:
            raise ValueError("write_indicator_value() can only be called on indicator result DataSeries")
        
        # Round the final result with symbol.digits (matching cTrader behavior)
        # This is the last step before returning calculated values to users
        digits = self._get_symbol_digits()
        rounded_value = round(value, digits)
        
        # Write rounded value to current position
        self.data[self._write_index] = rounded_value
        # Advance write index (circular)
        self._write_index = (self._write_index + 1) % self._size
    
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
        if self._parent.count == 0:
            return float("nan")
        return np.nanmean(self.data[: self._parent.count])  # type: ignore

    def get_max(self) -> float:
        """
        Compute the maximum of the current data in the buffer.
        """
        if self._parent.count == 0:
            return float("nan")
        return np.nanmax(self.data[: self._parent.count])  # type: ignore

    def get_min(self) -> float:
        """
        Compute the minimum of the current data in the buffer.
        """
        if self._parent.count == 0:
            return float("nan")
        return np.nanmin(self.data[: self._parent.count])  # type: ignore


# end of file
