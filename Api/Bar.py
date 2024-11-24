from datetime import datetime


class Bar:
    def __init__(
        self,
        open_time: datetime,
        open: float,
        high: float,
        low: float,
        close: float,
        tick_volume: int,
        open_ask: float,
    ):
        self.open_time = open_time
        self.open_price = open
        self.high_price = high
        self.low_price = low
        self.close_price = close
        self.tick_volume = tick_volume
        self.open_ask = open_ask