from abc import ABC, abstractmethod
from datetime import datetime
from AlgoApi import Symbol, Account, QuoteBar


class BrokerProvider(ABC):
    assets_file_name: str
    account: Account

    def __init__(self, account: Account, parameter: str):
        self.account = account
        self.parameter = parameter
        pass

    @abstractmethod
    def init(self, symbol: Symbol): ...

    @abstractmethod
    def get_quote_at_date(self, dt: datetime) -> tuple[str, QuoteBar]: ...

    @abstractmethod
    def get_next_quote(self) -> tuple[str, QuoteBar]: ...

    @abstractmethod
    def read_bar(self) -> tuple[str, QuoteBar]: ...

    @abstractmethod
    def update_account(self): ...
