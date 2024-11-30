import os
from datetime import datetime
from AlgoApi import Account, BrokerProvider, QuoteBar


class BrokerCsv(BrokerProvider):
    def __init__(self, parameter: str, data_rate: int, account: Account):
        super().__init__(parameter, data_rate, account)
        self.file_handle = None

    def __del__(self):
        if self.file_handle is not None:
            self.file_handle.close()

    def initialize(self, symbol_name: str):
        self.symbol_name = symbol_name
        self.symbol_path = os.path.join(self.parameter, self.symbol_name)
        pass

    def get_quote_bar_at_date(self, dt: datetime) -> tuple[str, QuoteBar]:
        return None  # type: ignore
        pass

    def get_first_quote_bar(self) -> tuple[str, QuoteBar]:
        return None  # type: ignore
        pass

    def get_next_quote_bar(self) -> tuple[str, QuoteBar]:
        return None  # type: ignore
        pass

    def read_quote_bar(self) -> tuple[str, QuoteBar]:
        return None  # type: ignore
        pass

    def update_account(self):
        pass
