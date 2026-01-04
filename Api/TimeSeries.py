from __future__ import annotations
from typing import TYPE_CHECKING, Iterator, Any
from datetime import datetime
import numpy as np
from Api.ring_buffer import Ringbuffer

if TYPE_CHECKING:
    from Api.Bars import Bars


class TimeSeries:
    data: Ringbuffer[datetime]
    _parent: Bars
    _size: int
    _add_count: int  # Total number of values added (linear count, for mapping absolute indices)

    def __init__(self, _parent: Bars, _size: int):
        """
        Initialize a TimeSeries with a ring buffer.
        """
        self._parent = _parent
        self._size = _size
        self._add_count = 0  # Track total number of values added (linear count)
        self.data = Ringbuffer[datetime](_size)  # Use true ringbuffer
    def resize(self, new_size: int) -> None:
        """
        Resize the underlying Ringbuffer while preserving existing data.
        """
        if new_size <= self._size:
            return
            
        old_buffer = self.data
        self._size = new_size
        self.data = Ringbuffer[datetime](new_size)
        
        # Copy data from old buffer (from oldest to newest)
        for i in range(old_buffer._count - 1, -1, -1):
            self.data.add(old_buffer[i])
        
        # _add_count remains the same (total added since start)


    def __iter__(self) -> Iterator[datetime]:
        """
        Iterate over the valid elements in the buffer.
        """
        # For Ringbuffer, iterate from oldest to newest
        count = min(self.data._count, self._parent.count)
        for i in range(count):
            rel_pos = count - 1 - i  # Convert to relative position (0 = most recent)
            if rel_pos < self.data._count:
                value = self.data[rel_pos]
                if value is not None:
                    yield value

    def append(self, value: datetime):
        """
        Append a single value to the ring buffer.
        Uses the ringbuffer's natural circular behavior (overwrites oldest when full).
        For tick data, this allows unbounded growth by using the ringbuffer's circular nature.
        """
        # Simply add to ringbuffer - it will overwrite oldest when full (circular behavior)
        self.data.add(value)
        self._add_count += 1
    
    def append_ring(self, value: datetime, position: int):
        """
        Append a value to a specific position in the ring buffer.
        Used for ring buffer mode where data overwrites oldest entries.
        For ringbuffer, we use add() which automatically handles circular indexing.
        """
        if position < 0 or position >= self._size:
            return  # Invalid position
        # For ringbuffer, we use add() which automatically handles circular indexing
        # If we need to set at a specific position, we need to use __setitem__
        # But append_ring is legacy - for new code, use add() directly
        self.data.add(value)
        self._add_count += 1  # Increment linear count

    def last(self, index: int) -> datetime:
        """
        Retrieve the last `index`-th element from the buffer.
        last(0) = current bar, last(1) = 1 bar ago, etc.
        Supports both sequential and ring buffer modes.
        """
        if index < 0 or index >= self._parent.count:
            return datetime.min
        
        # Use ringbuffer relative indexing
        # Map absolute index to relative position
        if self._parent.count <= self._size:
            # Sequential mode (buffer not full yet)
            # last(0) = most recent = ringbuffer[0]
            # last(1) = previous = ringbuffer[1]
            if index >= self.data._count:
                return datetime.min
            value = self.data[index]
        else:
            # Ring buffer is full - use circular indexing
            # Map to relative position
            if index >= self.data._count:
                return datetime.min
            value = self.data[index]
        
        if value is None:
            return datetime.min
        return value

    def __getitem__(self, index: int) -> datetime:
        """
        Access value at absolute index using [] operator (matching C# Source[index]).
        Maps absolute index to ring buffer position using _add_count.
        
        This allows code to use time_series[index] exactly like C# uses Source[index],
        with the ring buffer implementation transparently handling the mapping.
        
        Args:
            index: Absolute index (0, 1, 2, ...) - linear count from first value added
            
        Returns:
            Value at the specified absolute index, or datetime.min if index is out of range
        """
        if index < 0:
            return datetime.min
        
        # Map absolute index to ring buffer relative position
        # Ringbuffer uses relative indexing: [0] = most recent, [1] = second most recent, etc.
        # Absolute index i maps to relative position (_add_count - 1 - i)
        if index >= self._add_count:
            return datetime.min  # Index beyond what we've added
        
        # Check if value still exists (hasn't been overwritten)
        if self._add_count > self._size:
            # Buffer full - check if value was overwritten
            if index < self._add_count - self._size:
                return datetime.min  # Value was overwritten
        
        # Map absolute index to relative position
        # Absolute index 0 = oldest = relative position (_add_count - 1)
        # Absolute index (_add_count - 1) = newest = relative position 0
        rel_pos = self._add_count - 1 - index
        
        if rel_pos < 0 or rel_pos >= self.data._count:
            return datetime.min
        
        value = self.data[rel_pos]
        if value is None:
            return datetime.min
        return value


# end of file
