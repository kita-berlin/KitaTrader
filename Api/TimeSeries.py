from __future__ import annotations
from typing import TYPE_CHECKING
from typing import Iterable, Iterator
from datetime import datetime

if TYPE_CHECKING:
    from Api.Bars import Bars


class TimeSeries(Iterable[datetime]):
    def __init__(self, parent: Bars):
        self.parent = parent
        self.data: list[datetime] = []

    def __getitem__(self, index: int) -> datetime:
        return self.data[index]

    def __iter__(self) -> Iterator[datetime]:
        return iter(self.data)  # Generator for iteration

    # Access a value in the data series certain number of bars ago.
    def last(self, index: int) -> datetime:
        if index < 0 or index >= len(self.data):
            return datetime.min

        return self.data[self.parent.current - index]


# end of file
