from datetime import datetime
from BrokerProvider import BrokerProvider
from AlgoApi import Symbol, QuoteBar, Account


class BrokerPaper(BrokerProvider):
    def __init__(self, account: Account, parameter: str):
        super().__init__(account, parameter)

    def init(self, symbol: Symbol):
        pass

    def get_quote_at_date(self, dt: datetime) -> tuple[str, QuoteBar]:
        return None  # type: ignore
        pass

    def get_next_quote(self) -> tuple[str, QuoteBar]:
        return None  # type: ignore
        pass

    def read_bar(self) -> tuple[str, QuoteBar]:
        return None  # type: ignore
        pass

    def update_account(self):
        pass
