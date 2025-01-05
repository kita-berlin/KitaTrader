from datetime import datetime, timedelta
from Api.TradingSession import TradingSession


class MarketHours:
    @property
    def sessions(self) -> list[TradingSession]:
        # create list
        return list()

    # def is_opened(self) -> bool:
    #     pass

    # def is_opened(self, datetime: datetime) -> bool:
    #     pass

    def is_opened(self, datetime: datetime = None) -> bool:  # type:ignore
        if datetime is not None:  # type:ignore
            # Logic for checking if trading session is active at a specific datetime
            return True

        else:
            # Logic for checking if trading session is active at current time
            return True

    def time_till_close(self) -> timedelta:
        return timedelta.min

    def time_till_open(self) -> timedelta:
        return timedelta.min

    # end of file


# end of file
