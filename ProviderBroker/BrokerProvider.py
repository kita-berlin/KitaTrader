from abc import ABC, abstractmethod
from datetime import datetime
from Account import Account
from QuoteBar import QuoteBar
from AlgoApi import Symbol


class BrokerProvider(ABC):
    assets_file_name: str
    account: Account

    def __init__(self):
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
