from __future__ import annotations
from typing import TYPE_CHECKING
from typing import Iterable, Iterator
from Api.IIndicator import IIndicator

if TYPE_CHECKING:
    from Api.Bars import Bars


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
