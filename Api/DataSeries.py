from __future__ import annotations
from typing import TYPE_CHECKING
from typing import Iterable, Iterator
from Api.IIndicator import IIndicator
import numpy as np

if TYPE_CHECKING:
    from Api.Bars import Bars


import numpy as np
from typing import Iterator


class DataSeriesNp:
    def __init__(self, parent: Bars, initial_size: int = 1000):
        """
        Initialize a DataSeries with a dynamic buffer.
        """
        self.parent = parent
        self.size = initial_size
        self.data = np.full(self.size, np.nan)  # Pre-fill with NaN
        self.index = 0  # Tracks the current position
        self.count = 0  # Tracks the number of valid elements in the series

    def __getitem__(self, index: int) -> float:
        """
        Retrieve an item by its relative index.
        """
        if index < 0 or index >= self.count:
            return float("nan")
        return self.data[(self.index - self.count + index) % self.size]

    def __iter__(self) -> Iterator[float]:
        """
        Iterate over the valid elements in the buffer.
        """
        return iter(self.data[:self.count])

    def append(self, value: float):
        """
        Append a single value to the buffer, resizing dynamically if full.
        """
        if self.count == self.size:
            # Double the size of the buffer
            new_size = self.size * 2
            new_data = np.full(new_size, np.nan)

            # Copy existing data to the new buffer considering circular indexing
            if self.index >= self.count:  # Case: No wrap-around
                new_data[:self.count] = self.data[:self.count]
            else:  # Case: Wrap-around occurred
                part1 = self.data[self.index:]  # From index to end of the buffer
                part2 = self.data[:self.index]  # From start to index
                new_data[:self.count] = np.concatenate((part1, part2))

            self.data = new_data
            self.size = new_size
            self.index = self.count

        self.data[self.index] = value
        self.index = (self.index + 1) % self.size
        if self.count < self.size:
            self.count += 1


    def last(self, index: int) -> float:
        """
        Retrieve the last `index`-th element from the buffer.
        """
        if index < 0 or index >= self.count:
            return float("nan")
        return self.data[(self.index - index - 1) % self.size]

    def get_average(self) -> float:
        """
        Compute the average of the current data in the buffer.
        """
        if self.count == 0:
            return float("nan")
        return np.nanmean(self.data[:self.count]) # type: ignore

    def get_max(self) -> float:
        """
        Compute the maximum of the current data in the buffer.
        """
        if self.count == 0:
            return float("nan")
        return np.nanmax(self.data[:self.count])

    def get_min(self) -> float:
        """
        Compute the minimum of the current data in the buffer.
        """
        if self.count == 0:
            return float("nan")
        return np.nanmin(self.data[:self.count])


class DataSeries(Iterable[float]):
    def __init__(self, parent: Bars):
        self.parent = parent
        self.data: list[float] = []
        self.indicator_list: list[IIndicator] = []

    def __getitem__(self, index: int) -> float:
        if index < 0 or index >= len(self.data):
            return float("nan")

        return self.data[index]

    def __setitem__(self, index: int, value: float):
        if index < 0 or index >= len(self.data):
            return

        self.data[index] = value

    def __iter__(self) -> Iterator[float]:
        return iter(self.data)

    def append(self, value: float):
        self.data.append(value)
    
    def last(self, index: int) -> float:
        if index < 0 or index >= len(self.data):
            return float("nan")

        return self.data[self.parent.current - index]

    # Update indicators based on the current index.
    # def update_indicators(self, index: int, isNewBar: bool):
    #     for indi in self.indicator_list:
    #         while indi.index <= index:
    #             indi.is_last_bar = indi.index == index
    #             indi.calculate(indi.index)
    #             if indi.is_last_bar:
    #                 break
    #             else:
    #                 indi.index += 1


# end of file
