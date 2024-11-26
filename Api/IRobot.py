from abc import ABC, abstractmethod, abstractproperty, abstractclassmethod
from typing import TypeVar
from datetime import datetime
from KitaSymbol import Symbol

# Define a TypeVar that can be float or int
T = TypeVar("T", float, int)


###################################
class IRobot(ABC):
    symbol: Symbol

    ###################################
    @classmethod
    @abstractmethod
    def on_start(cls) -> None:
        pass

    ###################################
    @classmethod
    @abstractmethod
    def on_tick(cls) -> None:
        pass

    ###################################
    @classmethod
    @abstractmethod
    def on_stop(cls) -> None:
        pass

    ###################################
    @classmethod
    @abstractmethod
    def get_tick_fitness(cls) -> None:
        pass

    # Long/Short and other arithmetic
    # region
    @classmethod
    @abstractmethod
    def is_greater_or_equal_long(
        cls, long_not_short: bool, val1: float, val2: float
    ) -> bool:
        pass

    @classmethod
    @abstractmethod
    def is_less_or_equal_long(
        cls, long_not_short: bool, val1: float, val2: float
    ) -> bool:
        pass

    @classmethod
    @abstractmethod
    def is_greater_long(cls, long_not_short: bool, val1: float, val2: float) -> bool:
        pass

    @classmethod
    @abstractmethod
    def is_less_long(cls, long_not_short: bool, val1: float, val2: float) -> bool:
        pass

    @classmethod
    @abstractmethod
    def is_crossing(
        cls, long_not_short: bool, a_current: float, a_prev: float, b_current: float, b_prev: float
    ) -> bool:
        pass

    @classmethod
    @abstractmethod
    def add_long(cls, long_not_short: bool, val1: float, val2: float) -> bool:
        pass

    @classmethod
    @abstractmethod
    def sub_long(cls, long_not_short: bool, val1: float, val2: float) -> bool:
        pass

    @classmethod
    @abstractmethod
    def diff_long(cls, long_not_short: bool, val1: float, val2: float) -> bool:
        pass

    @classmethod
    @abstractmethod
    def i_price(cls, dPrice: float, tickSize: float) -> int:
        pass

    @classmethod
    @abstractmethod
    def d_price(cls, price: float, tickSize: float) -> float:
        pass

    @classmethod
    @abstractmethod
    def max(cls, ref_value: list[T], compare: T) -> bool:
        pass

    @classmethod
    @abstractmethod
    def min(cls, ref_value: list[T], compare: T) -> bool:
        pass

    @classmethod
    @abstractmethod
    def sharpe_sortino(cls, is_sortino: bool, vals: list[float]) -> float:
        pass

    @classmethod
    @abstractmethod
    def standard_deviation(cls, is_sortino: bool, vals: list[float]) -> float:
        pass

    @classmethod
    @abstractmethod
    def is_new_bar(cls, seconds: int, time: datetime, prevTime: datetime) -> bool:
        pass

    # endregion


# end of file
