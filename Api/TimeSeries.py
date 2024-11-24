import numpy as np
from typing import Iterable, Iterator
from datetime import datetime


# A series of values that represent time like market_series.open_time.
class TimeSeries(Iterable[datetime]):
    def __init__(self):
        self.data = np.array([], dtype="datetime64[D]")
        pass

    def __getitem__(
        self, index: int
    ) -> datetime:  # Returns the date_time value at the specified index.
        return self.data[index]

    def __iter__(self) -> Iterator[datetime]:
        return super().__iter__()

    @property
    def last_value(self) -> datetime:  # Gets the last value of this time series.
        return self.data[-1]

    @property
    def count(self) -> int:  # Gets the number of elements contained in the series.
        return len(self.data)

    def last(
        self, index: int
    ) -> datetime:  # Access a value in the data series certain number of bars ago.
        return self.data[self.count - index - 1]

    def get_index_by_exact_time(self, dateTime: datetime) -> int:
        """
        Find the index in the different time frame series.

        gui_parameters:
          dateTime:
            The open time of the bar at this index.
        """
        raise NotImplementedError

    def get_index_by_time(self, dateTime: datetime) -> int:
        """
        Find the index in the different time frame series.

        gui_parameters:
          dateTime:
            The open time of the bar at this index.
        """
        raise NotImplementedError
