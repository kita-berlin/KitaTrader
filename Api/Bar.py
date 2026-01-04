from datetime import datetime


class Bar:
    """
    Represents a single bar (OHLCV).
    Matches cTrader's Bar struct with properties: OpenTime, Open, High, Low, Close, TickVolume
    """
    def __init__(
        self,
        open_time: datetime = datetime.min,
        open: float = 0,
        high: float = 0,
        low: float = 0,
        close: float = 0,
        tick_volume: int = 0,
    ):
        
        self.OpenTime = open_time
        self.Open = open
        self.High = high
        self.Low = low
        self.Close = close
        self.TickVolume = tick_volume
        
        # Legacy properties (for backward compatibility)
        self.open_time = open_time
        self.open_bid = open
        self.high_bid = high
        self.low_bid = low
        self.close_bid = close
        self.volume_bid = tick_volume
        self.open_ask = open
        self.high_ask = high
        self.low_ask = low
        self.close_ask = close
        self.volume_ask = tick_volume


# end of file
