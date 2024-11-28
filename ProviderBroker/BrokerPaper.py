from datetime import datetime
from QuoteBar import QuoteBar
from BrokerProvider import BrokerProvider
from AlgoApi import Symbol
from Account import Account


class BrokerPaper(BrokerProvider):
    def __init__(self, account:Account):
        self.account = account
        pass

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
