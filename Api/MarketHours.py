from typing import List
from datetime import datetime, timedelta


class TradingSession:
    @property
    def start_time(self) -> datetime:
        return datetime.min

    @property
    def end_time(self) -> datetime:
        return datetime.min


class MarketHours:
    @property
    def sessions(self) -> List[TradingSession]:
        return List()

    # def is_opened(self) -> bool:
    #     pass

    # def is_opened(self, datetime: datetime) -> bool:
    #     pass

    def is_opened(self, datetime=None) -> bool:
        if datetime is not None:
            # Logic for checking if trading session is active at a specific datetime
            return True

        else:
            # Logic for checking if trading session is active at current time
            return True

    def time_till_close(self) -> timedelta:
        return timedelta.min

    def time_till_open(self) -> timedelta:
        return timedelta.min
