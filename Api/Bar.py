from datetime import datetime


class Bar:
    def __init__(
        self,
        open_time: datetime = datetime.min,
        open_bid: float = 0,
        high_bid: float = 0,
        low_bid: float = 0,
        close_bid: float = 0,
        volume_bid: float = 0,
        open_ask: float = 0,
        high_ask: float = 0,
        low_ask: float = 0,
        close_ask: float = 0,
        volume_ask: float = 0,
    ):
        self.open_time = open_time
        self.open_bid = open_bid
        self.high_bid = high_bid
        self.low_bid = low_bid
        self.close_bid = close_bid
        self.volume_bid = volume_bid
        self.open_ask = open_ask
        self.high_ask = high_ask
        self.low_ask = low_ask
        self.close_ask = close_ask
        self.volume_ask = volume_ask


# end of file
