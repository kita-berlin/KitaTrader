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

    def __init__(self, _parent: Bars, _size: int):
        """
        Initialize a DataSeries with a dynamic buffer.
        """
        self._parent = _parent
        self._size = _size
        self.data = np.full(self._size, np.nan)  # Pre-fill with NaN
        self.indicator_list = []  # List of indicators attached to this DataSeries

    def __getitem__(self, index: int) -> float:
        """
        Retrieve an item by its relative index.
        [0] = first bar, [1] = second bar, etc.
        Since data is stored sequentially via append(), we read directly from sequential positions.
        """
        if index < 0 or index >= self._parent.count:
            return float("nan")
        # Data is stored sequentially, so index directly maps to position
        return self.data[index]

    def __iter__(self) -> Iterator[float]:
        """
        Iterate over the valid elements in the buffer.
        """
        return iter(self.data[: self._parent.count])

    def append(self, value: float):
        """
        Append a single value to the buffer, resizing dynamically if full.
        """
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

    def last(self, index: int) -> float:
        """
        Retrieve the last `index`-th element from the buffer.
        last(0) = current bar, last(1) = 1 bar ago, etc.
        Since data is stored sequentially via append(), we read directly from sequential positions.
        """
        if index >= self._parent.count:
            return float("nan")
        # Data is stored sequentially: data[0] = first bar, data[count-1] = last bar
        # last(0) = current bar = data[count - 1]
        # last(1) = previous bar = data[count - 2]
        pos = self._parent.count - 1 - index
        if pos < 0 or pos >= len(self.data):
            return float("nan")
        return self.data[pos]

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
