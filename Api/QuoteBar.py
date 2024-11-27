from datetime import datetime


######################################
class QuoteBar:
    time: datetime = datetime.min
    milli_seconds: int = 0
    open: float = 0
    high: float = 0
    low: float = 0
    close: float = 0
    volume: int = 0
    open_ask: float = 0
