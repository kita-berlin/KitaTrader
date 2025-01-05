from __future__ import annotations
from abc import ABC, abstractmethod
from Api.Symbol import Symbol
from Api.KitaApiEnums import *
from Api.TradeResult import *
from Api.Position import Position


class TradeProvider(ABC):
    api: KitaApi

    def __init__(self, parameter: str):
        self.parameter = parameter
        pass

    @abstractmethod
    def init_symbol(self, api: KitaApi, symbol: Symbol, cache_path: str = ""): ...

    @abstractmethod
    def update_account(self): ...

    @abstractmethod
    def add_profit(self, profit: float): ...

    @abstractmethod
    def execute_market_order(
        self, trade_type: TradeType, symbol_name: str, volume: float, label: str = ""
    ) -> Position: ...

    def close_position(self, pos: Position) -> TradeResult: ...


# end of file
