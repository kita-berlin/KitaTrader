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


    def __getitem__(self, index: int) -> datetime:
        """
        Retrieve a datetime object by its relative index.
        """
        if index < 0 or index >= self._parent.count:
            return datetime.min
        return self.data[(self._parent.read_index + index - 1) % self._size]

    def __iter__(self) -> Iterator[datetime]:
        """
        Iterate over the valid elements in the buffer.
        """
        return iter(self.data[: self._parent.count])

    def append(self, value: datetime):
        """
        Append a single value to the buffer, resizing dynamically if full.
        """
        if self._parent.count == self._size:
            # Double the _size of the buffer
            new_size = self._size * 2
            new_data = np.full(new_size, datetime.min, dtype=datetime)

            part1 = self.data[self._parent.count :]  # From index to end of the buffer
            part2 = self.data[: self._parent.count]  # From start to index
            new_data[: self._size] = np.concatenate((part1, part2))  # type: ignore

            self.data = new_data
            self._size = new_size

        self.data[self._parent.count] = value

    def last(self, index: int) -> datetime:
        """
        Retrieve the last `index`-th element from the buffer.
        """
        if index >= self._parent.count:
            return datetime.min
        # The data is appended sequentially.
        # read_index points to the current active bar index (0 to count-1)
        # last(0) calls for data at read_index
        # last(1) calls for data at read_index - 1
        return self.data[(self._parent.read_index - index) % self._size]


# end of file
