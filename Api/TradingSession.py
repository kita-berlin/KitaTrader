from datetime import datetime


class TradingSession:
    @property
    def start_time(self) -> datetime:
        return datetime.min

    @property
    def end_time(self) -> datetime:
        return datetime.min

    # end of file
