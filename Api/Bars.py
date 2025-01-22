from __future__ import annotations
from datetime import datetime
from Api.TimeSeries import TimeSeries
from Api.DataSeries import DataSeries
from Api.KitaApiEnums import *


class Bars:
    # bars are not indexed; only time and data series are indexed
    # Do not use bars.Last().open_time; Use bars.open_times.Last() instead

    # Members
    # region
    open_times: TimeSeries

    open_bids: DataSeries
    high_bids: DataSeries
    low_bids: DataSeries
    close_bids: DataSeries
    volume_bids: DataSeries

    open_asks: DataSeries
    high_asks: DataSeries
    low_asks: DataSeries
    close_asks: DataSeries
    volume_asks: DataSeries

    symbol_name: str  # Gets the symbol name
    timeframe_seconds: int  # Get the timeframe in seconds
    look_back: int  # Gets the look back period.#
    is_new_bar: bool = False  # if true, the current tick is the first tick of a new bar
    read_index: int = 0  # relative index of the current bar to be read
    count: int = 0  # number of bars appended so far; if count == size, the buffer is completely filled
    data_mode: DataMode

    @property
    def size(self) -> int:  # Gets the number of bars.#
        return len(self.open_times.data)  # type: ignore

    # endregion

    def __init__(self, symbol_name: str, timeframe_seconds: int, look_back: int, data_mode: DataMode):
        self.symbol_name = symbol_name
        self.timeframe_seconds = timeframe_seconds
        self.look_back = look_back
        self.data_mode = data_mode
        self.read_index = 0  # gets a +1 at symbol_on_tick before accessing the data
        size = 1000  # initial size of the buffer

        # Create initial OHLC data
        self.open_times = TimeSeries(self, size)
        self.open_bids = DataSeries(self, size)
        self.open_asks = DataSeries(self, size)
        self.volume_bids = DataSeries(self, size)
        self.volume_asks = DataSeries(self, size)
        if 0 != timeframe_seconds:
            self.high_bids = DataSeries(self, size)
            self.low_bids = DataSeries(self, size)
            self.close_bids = DataSeries(self, size)

            self.high_asks = DataSeries(self, size)
            self.low_asks = DataSeries(self, size)
            self.close_asks = DataSeries(self, size)

    def append(
        self,
        time: datetime,
        open_bid: float,
        high_bid: float,
        low_bid: float,
        close_bid: float,
        volume_bid: float,
        open_ask: float,
        high_ask: float,
        low_ask: float,
        close_ask: float,
        volume_ask: float,
    ) -> None:
        self.open_times.append(time)
        self.open_bids.append(open_bid)
        self.open_asks.append(open_ask)
        self.volume_bids.append(volume_bid)
        self.volume_asks.append(volume_ask)
        if 0 != self.timeframe_seconds:
            self.high_bids.append(high_bid)
            self.low_bids.append(low_bid)
            self.close_bids.append(close_bid)
            self.high_asks.append(high_ask)
            self.low_asks.append(low_ask)
            self.close_asks.append(close_ask)

        self.count += 1

    def add(
        self,
        time: datetime,
        open_bid: float,
        high_bid: float,
        low_bid: float,
        close_bid: float,
        volume_bid: float,
        open_ask: float,
        high_ask: float,
        low_ask: float,
        close_ask: float,
        volume_ask: float,
    ) -> None:

        # xxxxx todo

        self.read_index = (self.read_index + 1) % self.open_times._size  # type: ignore
        if self.count < self.open_times._size:  # type: ignore
            self.count += 1

    def bars_on_tick(self, time: datetime) -> None:
        self.is_new_bar = False

        if DataMode.Preload == self.data_mode:
            # synchronize the bars with  the tick time open time by setting their read_index index
            while self.read_index < self.count and time >= self.open_times.last(-1):
                self.read_index += 1
                self.is_new_bar = True
        else:
            pass

        # if False:
        #     # do we have to build a new bar ?
        #     if (
        #         0 == self.open_times.count  # on init
        #         or 0 == self.timeframe_seconds  # tick data rate
        #         or self.is_new_bar_get(
        #             self.timeframe_seconds, bar.open_time, self.open_times.data[-1]
        #         )  # new bar ?
        #     ):
        #         self.open_times.data.append(bar.open_time)
        #         self.open_bids.data.append(bar.open_price)
        #         self.open_asks.data.append(bar.open_ask)
        #         if 0 != self.timeframe_seconds:
        #             self.high_bids.data.append(bar.open_price)
        #             self.low_bids.data.append(bar.open_price)
        #             self.close_bids.data.append(bar.open_price)
        #             self.volume.data.append(0)

        #         self.is_new_bar = True
        #     else:
        #         self.high_bids.data[-1] = max(self.high_bids.data[-1], bar.high_price)
        #         self.low_bids.data[-1] = min(self.low_bids.data[-1], bar.low_price)
        #         self.close_bids.data[-1] = bar.close_price
        #         self.volume.data[-1] += 1 if 0 == bar.volume else bar.volume

        # self.open_bids.update_indicators(self.open_times.count - 1, self.is_new_bar)
        # self.high_bids.update_indicators(self.open_times.count - 1, self.is_new_bar)
        # self.low_bids.update_indicators(self.open_times.count - 1, self.is_new_bar)
        # self.close_bids.update_indicators(self.open_times.count - 1, self.is_new_bar)
        # self.volume.update_indicators(self.open_times.count - 1, self.is_new_bar)
        # self.open_asks.update_indicators(self.open_times.count - 1, self.is_new_bar)
        return


# end of file
