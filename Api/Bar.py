from datetime import datetime


class Bar:
    def __init__(
        self,
        open_time: datetime = datetime.min,
        open: float = 0,
        high_time: datetime = datetime.min,
        high: float = 0,
        low_time: datetime = datetime.min,
        low: float = 0,
        close: float = 0,
        volume: float = 0,
        open_ask: float = 0,
    ):
        self.open_time = open_time
        self.open_price = open
        self.high_time = high_time
        self.high_price = high
        self.low_time = low_time
        self.low_price = low
        self.close_price = close
        self.volume = volume
        self.open_ask = open_ask


# end of file
