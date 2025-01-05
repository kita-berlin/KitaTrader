from typing import Iterable, Iterator
from Api.IIndicator import IIndicator


class DataSeries(Iterable[float]):
    def __init__(self):
        self.indicator_list: list[IIndicator] = []
        self.data: list[float] = []

    def __getitem__(self, index: int) -> float:
        if index < 0:
            index += len(self.data)
        if index >= len(self.data) or index < 0:
            raise IndexError("Index out of range")
        return self.data[index]

    def __setitem__(self, index: int, value: float):
        """Set the value at a specific index in the data series."""
        if index < 0:
            index += len(self.data)

        if index == len(self.data):
            self.data.append(0)

        if index >= len(self.data) or index < 0:
            raise IndexError("Index out of range")
        self.data[index] = value

    def __iter__(self) -> Iterator[float]:
        return iter(self.data)

    @property
    def last_value(self) -> float:
        """Gets the last value of this DataSeries."""
        if self.count == 0:
            raise IndexError("DataSeries is empty, no last value available.")
        return self.data[-1]

    @property
    def count(self) -> int:
        """Gets the number of elements contained in the series."""
        return len(self.data)

    def last(self, index: int) -> float:
        """Access a value in the dataseries certain bars ago."""
        if index < 0 or index >= self.count:
            raise IndexError("Index out of range for last()")
        return self.data[self.count - index - 1]

    def append(self, value: float):
        """Append a new value to the DataSeries."""
        self.data.append(value)

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
