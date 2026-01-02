from __future__ import annotations
from typing import TYPE_CHECKING, Iterator, Any
from datetime import datetime
import numpy as np

if TYPE_CHECKING:
    from Api.Bars import Bars


class TimeSeries:
    data: np.ndarray[Any, object]  # type: ignore
    _parent: Bars
    _size: int

    def __init__(self, _parent: Bars, _size: int):
        """
        Initialize a TimeSeries with a dynamic buffer.
        """
        self._parent = _parent
        self._size = _size
        self.data = np.full(self._size, None, dtype=object)


    def __iter__(self) -> Iterator[datetime]:
        """
        Iterate over the valid elements in the buffer.
        """
        return iter(self.data[: self._parent.count])

    def append(self, value: datetime):
        """
        Append a single value to the buffer (legacy method - use append_ring for ring buffers).
        For ring buffers, use append_ring() instead.
        """
        # Legacy behavior: resize if full (for backward compatibility)
        if self._parent.count == self._size:
            # Double the _size of the buffer
            new_size = self._size * 2
            new_data = np.full(new_size, datetime.min, dtype=object)

            part1 = self.data[self._parent.count :]  # From index to end of the buffer
            part2 = self.data[: self._parent.count]  # From start to index
            new_data[: self._size] = np.concatenate((part1, part2))  # type: ignore

            self.data = new_data
            self._size = new_size

        self.data[self._parent.count] = value
    
    def append_ring(self, value: datetime, position: int):
        """
        Append a value to a specific position in the ring buffer.
        Used for ring buffer mode where data overwrites oldest entries.
        """
        if position < 0 or position >= self._size:
            return  # Invalid position
        self.data[position] = value

    def last(self, index: int) -> datetime:
        """
        Retrieve the last `index`-th element from the buffer.
        last(0) = current bar, last(1) = 1 bar ago, etc.
        Supports both sequential and ring buffer modes.
        """
        if index < 0 or index >= self._parent.count:
            return datetime.min
        
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
        
        result = self.data[pos] if pos < len(self.data) and self.data[pos] is not None else datetime.min
        return result


# end of file
