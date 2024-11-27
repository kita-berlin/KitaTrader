
class TradeResult:
    def __init__(self, is_successful: bool = True, error: str = None):  # type: ignore
        self.is_successful = is_successful
        self.error = error
