from __future__ import annotations
from typing import TYPE_CHECKING
from typing import Iterable, Iterator, Any
from datetime import datetime
import numpy as np

if TYPE_CHECKING:
    from Api.Bars import Bars


class TimeSeriesNp:
    def __init__(self, parent: Bars, initial_size: int = 1000):
        """
        Initialize a TimeSeries with a dynamic buffer.
        """
        self.parent: "Bars" = parent
        self.size: int = initial_size
        self.data: np.ndarray[Any, object] = np.full(self.size, None, dtype=object)
        self.index: int = 0  # Tracks the current position
        self.count: int = 0  # Tracks the number of valid elements in the series

    def __getitem__(self, index: int) -> datetime:
        """
        Retrieve a datetime object by its relative index.
        """
        if index < 0 or index >= self.count:
            return datetime.min
        return self.data[(self.index - self.count + index) % self.size]

    def __iter__(self) -> Iterator[datetime]:
        """
        Iterate over the valid elements in the buffer.
        """
        return iter(self.data[: self.count])

    def append(self, value: datetime):
        """
        Append a single value to the buffer, resizing dynamically if full.
        """
        if self.count == self.size:
            # Double the size of the buffer
            new_size = self.size * 2
            new_data = np.full(new_size, datetime.min, dtype=datetime)

            # Copy existing data to the new buffer considering circular indexing
            if self.index >= self.count:  # Case: No wrap-around
                new_data[: self.count] = self.data[: self.count]
            else:  # Case: Wrap-around occurred
                part1 = self.data[self.index :]  # From index to end of the buffer
                part2 = self.data[: self.index]  # From start to index
                new_data[: self.count] = np.concatenate((part1, part2))

            self.data = new_data
            self.size = new_size
            self.index = self.count

        self.data[self.index] = value
        self.index = (self.index + 1) % self.size
        if self.count < self.size:
            self.count += 1

    def last(self, index: int) -> datetime:
        """
        Retrieve the last `index`-th element from the buffer.
        """
        if index < 0 or index >= self.count:
            return datetime.min
        return self.data[(self.index - index - 1) % self.size]


class TimeSeries(Iterable[datetime]):
    def __init__(self, parent: Bars):
        self.parent = parent
        self.data: list[datetime] = []

    def __getitem__(self, index: int) -> datetime:
        return self.data[index]

    def __iter__(self) -> Iterator[datetime]:
        return iter(self.data)  # Generator for iteration

    def append(self, value: datetime):
        self.data.append(value)

    # Access a value in the data series certain number of bars ago.
    def last(self, index: int) -> datetime:
        if index < 0 or index >= len(self.data):
            return datetime.min

        return self.data[self.parent.current - index]


# end of file
