import numpy as np
from typing import Iterable, Iterator

# from indicators import i_indicator


# Represents a read only list of values, typically used to represent market price
# series. The values are accessed with an array-like [] operator.
class DataSeries(Iterable[float]):
    indicator_list = []
    data: np.array = []

    def __init__(self):
        self.data = np.array([], dtype=np.float64)
        pass

    # Gets the value in the dataseries at the specified Position.
    def __getitem__(self, index: int) -> float:
        # Handle negative indexing
        if index < 0:
            index += len(self.data)

        # Check for index out of range
        if index >= len(self.data) or index < 0:
            raise IndexError("Index out of range")

        return self.data[index]

    def __setitem__(self, index, value):
        # Handle negative indexing
        if index < 0:
            index += len(self.data)

        # Check for index out of range
        if index < 0:
            raise IndexError("Index out of range")

        if index >= len(self.data):
            self.data = np.append(self.data, value)
        else:
            self.data[index] = value
        pass

    def __iter__(self) -> Iterator[float]:
        return super().__iter__()

    """
    Remarks:
        The last value may represent one of the values of the last bar of the market
        series, e.g. Open, High, Low and Close. Therefore, take into consideration that
        on each tick, except the Open price, the rest of the values will most probably
        change.
    """

    @property
    def last_value(self) -> float:  # Gets the last value of this DataSeries.
        return self.data[-1]

    @property
    def count(self) -> int:  # Gets the number of elements contained in the series.
        return len(self.data)

    def last(
        self, index: int
    ) -> float:  # Access a value in the dataseries certain bars ago.
        return self.data[self.count - index - 1]

    def update_indicators(self, index: int, isNewBar: bool):
        for indi in self.indicator_list:
            while indi._index <= index:
                indi.is_last_bar = indi._index == index
                indi.calculate(indi._index)
                if indi.is_last_bar:
                    break
                else:
                    indi._index += 1
        pass


# end of file