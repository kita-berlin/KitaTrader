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
        
        The 'position' parameter is the write_pos from bars.append(), which is the absolute position
        in the bar buffer. We need to convert it to the relative position in the DataSeries ringbuffer.
        Since the DataSeries ringbuffer should be in sync with the bar buffer, the newest bar should
        always be at relative position 0. So we need to convert write_pos to relative position 0.
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
            # add() places the value at the current _position and advances it sequentially
            # The 'position' parameter is write_pos from bars.append(), which is informational only.
            # The DataSeries ringbuffer maintains its own independent _position that wraps naturally.
            # The absolute index mapping in __getitem__ handles the translation correctly.
            self.data.add(value)
        else:
            # _add_count already matches parent count - this is a duplicate call for the same bar
            # Update the value at the current newest position (relative position 0)
            if self.data._count > 0:
                # Update relative position 0 (newest value)
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
        # For indicator results, use absolute indexing via __getitem__ to ensure correct mapping
        if self._is_indicator_result:
            # For indicator results, we need to use the source DataSeries's _add_count, not _parent.count
            # because _parent.count only includes backtest bars, while _add_count includes warmup bars
            source_dataseries = None
            if self._owner_indicator and hasattr(self._owner_indicator, 'source'):
                source_dataseries = self._owner_indicator.source
            
            # CRITICAL: Always use source DataSeries's _add_count for indicator results
            # The result's _add_count may lag behind if indicators are calculated out of order
            if source_dataseries and hasattr(source_dataseries, '_add_count'):
                source_add_count = source_dataseries._add_count
            else:
                # Fallback: use self._add_count, but this might be wrong if indicators calculated out of order
                source_add_count = self._add_count
            
            # The 'index' parameter in last() is "bars ago from newest" (0 = newest, 1 = 1 bar ago, etc.)
            # In C#, series[index] where index = Bars.Count - 2 uses relative indexing (0 = newest)
            # But Bars.Count in C# includes warmup bars, while _parent.count in Python is only backtest bars
            # So we need to convert: if newest bar is at absolute index (source_add_count - 1),
            # then "index bars ago" is at absolute index (source_add_count - 1 - index)
            # This matches the original formula: abs_index = total_count - 1 - index
            abs_index = max(0, source_add_count - 1 - index)
            
            # Validate abs_index against source to ensure we're not reading beyond what exists
            if abs_index < 0 or abs_index >= source_add_count:
                return float("nan")
            
            # CRITICAL: When buffer is NOT full (add_count < size), result's _add_count should match source's
            # But if indicators are calculated out of order, result's _add_count might be smaller
            # In that case, lazy calculation should fill the gap, but we still need to validate
            result_add_count = self._add_count
            
            if self._owner_indicator and hasattr(self._owner_indicator, 'lazy_calculate'):
                self._owner_indicator.lazy_calculate(abs_index)
            # Use __getitem__ with absolute index to get the correct value
            # This ensures the absolute->relative conversion is done correctly
            try:
                value = self[abs_index]
                return float(value) if not np.isnan(value) else float('nan')
            except (IndexError, KeyError):
                return float("nan")
        
        # For non-indicator DataSeries, use direct ringbuffer access (relative indexing)
        if index < 0 or index >= self._parent.count:
            return float("nan")
                
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
        
        
        # No rounding for indicator results - maintain full precision
        rounded_value = value if not np.isnan(value) else float('nan')
        
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
        # For indicator results, trigger lazy calculation if requested and possible
        # CRITICAL: Do this BEFORE checking _add_count, so lazy calculation can update it
        if self._is_indicator_result and self._owner_indicator:
            if hasattr(self._owner_indicator, 'lazy_calculate'):
                # Debug: Log lazy calculation trigger for H1/H4 or early indices
                if hasattr(self._owner_indicator, 'source') and hasattr(self._owner_indicator.source, '_parent'):
                    tf_seconds = getattr(self._owner_indicator.source._parent, 'timeframe_seconds', 0)
                    if tf_seconds in [3600, 14400] or index < 50:
                        if hasattr(self._owner_indicator.source._parent, '_symbol') and hasattr(self._owner_indicator.source._parent._symbol, 'api'):
                            api = self._owner_indicator.source._parent._symbol.api
                            if hasattr(api, 'robot') and hasattr(api.robot, '_debug_log'):
                                tf_name = "H1" if tf_seconds == 3600 else "H4" if tf_seconds == 14400 else f"{tf_seconds}s"
                                api.robot._debug_log(f"[DataSeries] Triggering lazy_calculate for {tf_name} at index={index}")
                self._owner_indicator.lazy_calculate(index)
                # After lazy calculation, _add_count might have been updated
                # Re-check if index is now valid

        if index < 0 or index >= self._add_count:
            return float("nan")
        
        # Check if value still exists (hasn't been overwritten)
        # When buffer is full (_count == _size), values older than (_add_count - _size) were overwritten
        # When buffer is not full (_count < _size), all values from index 0 to (_add_count - 1) are accessible
        if self.data._count == self.data._size and self._add_count > self.data._size:
            # Buffer is full - check if index was overwritten
            oldest_abs_index = self._add_count - self.data._size
            if index < oldest_abs_index:
                return float("nan")  # Value was overwritten
        
        # Absolute index i maps to relative position (rel_pos)
        # Use ring buffer's add_count as the linear index counter
        # Formula: rel_pos = (newest_abs_index) - index
        # Where newest_abs_index = _add_count - 1 (0-indexed, so _add_count=31 means newest is at abs_index 30)
        # Verify index is valid for this DataSeries
        if index >= self.data._add_count:
            # Index is beyond what this DataSeries has - use the newest available index
            index = self.data._add_count - 1
        
        rel_pos = (self.data._add_count - 1) - index
        
        # CRITICAL: When buffer is NOT full (_count < _size), _count == _add_count (linear growth)
        # When buffer IS full (_count == _size), _count == _size and _add_count >= _size (rotation)
        # For non-full buffers, rel_pos must be < _count (which equals _add_count)
        # For full buffers, rel_pos can be < _size (but we validate against _count which equals _size)
        
        # Additional validation: rel_pos should be within the valid range
        # The oldest accessible value depends on whether the buffer is full
        # If buffer is full (_count == _size), oldest is at (_add_count - _size)
        # If buffer is not full (_count < _size), oldest is at 0 (all values are accessible)
        if self.data._count == self.data._size:
            # Buffer is full - use _size to determine oldest accessible index
            oldest_abs_index = self.data._add_count - self.data._size
        else:
            # Buffer not full - all values from 0 to (_add_count - 1) are accessible
            # In this case, _count == _add_count, so rel_pos should be in [0, _count-1]
            oldest_abs_index = 0
        if index < oldest_abs_index:
            return float("nan")  # Value was overwritten
        
        # CRITICAL FIX: Validate rel_pos based on buffer state
        # When buffer is NOT full (_count < _size): _count == _add_count, so rel_pos must be < _count
        # When buffer IS full (_count == _size): rel_pos must be < _size (which equals _count)
        # The ringbuffer.__getitem__ also checks rel_pos < _size, so we validate against _count
        # (which is <= _size) and let ringbuffer handle the _size check
        # CRITICAL: For non-full buffers, rel_pos can be in [0, _count-1] where _count == _add_count
        # For full buffers, rel_pos can be in [0, _size-1] where _size == _count
        # So the check `rel_pos < _count` works for both cases
        if 0 <= rel_pos < self.data._count:
            # CRITICAL: For non-full buffers, use the correct physical position calculation
            # The ringbuffer.__getitem__ already handles this correctly, but we need to ensure
            # we're using the right formula for logging
            if self.data._count < self.data._size:
                # Non-full buffer: physical_pos = (_position - 1 - rel_pos) % _size
                ringbuffer_abs_pos = (self.data._position - 1 - rel_pos) % self.data._size if rel_pos > 0 else ((self.data._position - 1) % self.data._size if self.data._position > 0 else 0)
            else:
                # Full buffer: use standard formula
                pass
            
            value = self.data[rel_pos]
            if value is None:
                return float("nan")
            result = float(value) if not np.isnan(value) else float('nan')
            return result
        
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
            
            # Use ring buffer's add_count as the linear index counter
            rel_pos = (self.data._add_count - 1) - index
            
            # CRITICAL: When buffer is NOT full (_count < _size), _count == _add_count
            # When buffer IS full (_count == _size), _count == _size
            # For non-full buffers, rel_pos must be < _count (which equals _add_count)
            # For full buffers, rel_pos must be < _size (which equals _count)
            # The ringbuffer.__setitem__ expects rel_pos < _size, so we validate against _count
            # (which is <= _size) and let ringbuffer handle the _size check
            if 0 <= rel_pos < self.data._count:
                # No rounding for indicator results - maintain full precision
                new_value = value if not np.isnan(value) else float('nan')
                self.data[rel_pos] = new_value
                # Update _last_calc_index when updating existing values (important for recursive indicators like EMA)
                if self._is_indicator_result and index > self._last_calc_index:
                    self._last_calc_index = index
        else:
            # index > _add_count: Gap! Fill with NaNs
            # CRITICAL: When filling gaps, we need to ensure _add_count matches the source's _add_count
            # to prevent reading NaNs when accessing historical values
            # However, we can't access the source here, so we'll just fill up to the requested index
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
