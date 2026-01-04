from __future__ import annotations
from typing import TYPE_CHECKING, Iterator, Any
from datetime import datetime
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
        self.data = Ringbuffer[float](_size)  # Use true ringbuffer - its _add_count is the linear index counter
        self.indicator_list = []  # List of indicators attached to this DataSeries
        self._owner_indicator = None  # The indicator that produces this DataSeries as a result
        self._last_calc_index = -1  # Last absolute index calculated for this indicator result
    
    @property
    def _add_count(self) -> int:
        """
        Get the linear index counter from the ring buffer's add_count.
        This is the total number of values added (linear count, for mapping absolute indices).
        """
        return self.data._add_count
    
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
        # The ring buffer's add() method increments its _add_count automatically
        self.data.add(value)
    
    def append_ring(self, value: float, position: int):
        """
        Append a value to sync DataSeries with the bar buffer.
        Used by bar generation to sync DataSeries with the bar buffer.
        
        IMPORTANT: This is called for EVERY DataSeries (11 times per bar: open_times, open_bids, etc.).
        We should only increment _add_count ONCE per bar, not once per DataSeries.
        
        The fix: Only increment _add_count if it's less than the parent's bar count.
        This ensures _add_count equals the number of bars, not the number of append_ring calls.
        """
        if position < 0 or position >= self._size:
            return  # Invalid position
        
        # Get parent bar count logic adapted for infinite stream vs ring buffer
        parent_count = 0
        if hasattr(self._parent, '_bar_buffer') and self._parent._bar_buffer:
             parent_count = self._parent._bar_buffer._add_count
        elif hasattr(self._parent, 'count'):
             parent_count = self._parent.count
        
        # Only increment _add_count if it's less than the parent's bar count
        # This ensures _add_count equals the number of bars, not the number of append_ring calls
        # Since append_ring is called 11 times per bar, this ensures we only increment once per bar
        if self.data._add_count < parent_count:
            # This is a new bar - increment _add_count by calling add()
            self.data.add(value)
        else:
            # _add_count already matches parent count - this is a duplicate call for the same bar
            # Just update the value at the newest position (relative position 0)
            if self.data._count > 0:
                self.data[0] = value
            else:
                # Empty buffer - use add()
                self.data.add(value)

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
        Write a value to the indicator result ring buffer.
        Equivalent to cTrader's logic when a value is appended to an IndicatorDataSeries.
        The ring buffer's add() method increments its _add_count automatically.
        """
        if not self._is_indicator_result:
            raise ValueError("write_indicator_value() can only be called on indicator result DataSeries")
        
        
        digits = self._get_symbol_digits()
        rounded_value = round(value, digits) if not np.isnan(value) else float('nan')
        
        # Simply append to the ringbuffer - it increments _add_count automatically
        self.data.add(rounded_value)
        self._last_calc_index = self.data._add_count - 1

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
        # Debug logging for first few accesses
        debug_log = getattr(self, '_debug_log_func', None)
        if debug_log and (index < 5 or index % 100 == 0):
            debug_log(f"DataSeries.__getitem__(index={index}): _is_indicator_result={self._is_indicator_result}, _add_count={self._add_count}, _size={self._size}, data._count={self.data._count}")
        
        # For indicator results, trigger lazy calculation if requested and possible
        if self._is_indicator_result and self._owner_indicator:
            if hasattr(self._owner_indicator, 'lazy_calculate'):
                if debug_log and (index < 5 or index % 100 == 0):
                    debug_log(f"DataSeries.__getitem__: calling lazy_calculate({index})")
                self._owner_indicator.lazy_calculate(index)

        if index < 0 or index >= self._add_count:
            if debug_log and (index < 5 or index % 100 == 0):
                debug_log(f"DataSeries.__getitem__: index {index} out of range (_add_count={self._add_count}), returning NaN")
            return float("nan")
        
        # Check if value still exists (hasn't been overwritten)
        if self._add_count > self._size:
            if index < self._add_count - self._size:
                if debug_log and (index < 5 or index % 100 == 0):
                    debug_log(f"DataSeries.__getitem__: index {index} was overwritten, returning NaN")
                return float("nan")  # Value was overwritten
        
        # Absolute index i maps to relative position (rel_pos)
        # Use ring buffer's add_count as the linear index counter
        rel_pos = (self.data._add_count - 1) - index
        
        if 0 <= rel_pos < self.data._count:
            value = self.data[rel_pos]
            if value is None:
                if debug_log and (index < 5 or index % 100 == 0):
                    debug_log(f"DataSeries.__getitem__: value at rel_pos {rel_pos} is None, returning NaN")
                return float("nan")
            result = float(value) if not np.isnan(value) else float('nan')
            if debug_log and (index < 5 or index % 100 == 0):
                debug_log(f"DataSeries.__getitem__: returning value={result} from rel_pos={rel_pos}")
            return result
        
        if debug_log and (index < 5 or index % 100 == 0):
            debug_log(f"DataSeries.__getitem__: rel_pos {rel_pos} out of range (data._count={self.data._count}), returning NaN")
        return float("nan")

    def __setitem__(self, index: int, value: float):
        """
        Set value at absolute index i (matching C# Result[index] = value).
        If index == _add_count, it appends a new value.
        If index < _add_count, it updates an existing (non-overwritten) value.
        """
        # Debug logging for first few sets
        debug_log = getattr(self, '_debug_log_func', None)
        if debug_log and (index < 5 or index % 100 == 0):
            debug_log(f"DataSeries.__setitem__(index={index}, value={value}): _add_count={self._add_count}, _size={self._size}, data._count={self.data._count}")
        
        if index < 0:
            if debug_log and (index < 5 or index % 100 == 0):
                debug_log(f"DataSeries.__setitem__: index {index} < 0, returning")
            return
            
        if index == self._add_count:
            # Append mode
            if debug_log and (index < 5 or index % 100 == 0):
                debug_log(f"DataSeries.__setitem__: append mode (index == _add_count)")
            self.write_indicator_value(value)
        elif index < self._add_count:
            # Update mode
            if self._add_count > self._size:
                if index < self._add_count - self._size:
                    if debug_log and (index < 5 or index % 100 == 0):
                        debug_log(f"DataSeries.__setitem__: index {index} already overwritten, returning")
                    return # Value already overwritten in ringbuffer
            
            # Use ring buffer's add_count as the linear index counter
            rel_pos = (self.data._add_count - 1) - index
            if 0 <= rel_pos < self.data._count:
                rounded_value = round(value, self._get_symbol_digits()) if not np.isnan(value) else float('nan')
                if debug_log and (index < 5 or index % 100 == 0):
                    debug_log(f"DataSeries.__setitem__: update mode, setting rel_pos={rel_pos} to {rounded_value}")
                self.data[rel_pos] = rounded_value
        else:
            # index > _add_count: Gap! Fill with NaNs
            if debug_log and (index < 5 or index % 100 == 0):
                debug_log(f"DataSeries.__setitem__: gap mode (index {index} > _add_count {self._add_count}), filling with NaNs")
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
