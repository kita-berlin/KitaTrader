from __future__ import annotations
from datetime import datetime
from Api.Bar import Bar
from Api.TimeSeries import TimeSeries
from Api.DataSeries import DataSeries


class Bars:
    # bars are not indexed; only time and data series are indexed
    # Do not use bars.Last().open_time; Use bars.open_times.Last() instead

    # Members
    # region
    symbol_name: str  # Gets the symbol name.#
    timeframe_seconds: int  # Get the timeframe in seconds.#
    look_back: int  # Gets the look back period.#
    open_times: TimeSeries  # Gets the open bar time data.#
    open_bids: DataSeries  # Gets the Open price bars data.#
    high_bids: DataSeries  # Gets the High price bars data.#
    low_bids: DataSeries  # Gets the Low price bars data.#
    close_bids: DataSeries  # Gets the Close price bars data.#
    volume: DataSeries  # Gets the tick volumes data.#
    open_asks: DataSeries  # The ask value at open time (open_bids are bids)
    is_new_bar: bool = False  # if true, the current tick is the first tick of a new bar
    current: int = 0  # index of the current bar

    @property
    def count(self) -> int:  # Gets the number of bars.#
        return self.current + 1

    # endregion

    def __init__(self, symbol_name: str, timeframe_seconds: int, look_back: int):
        self.symbol_name = symbol_name
        self.timeframe_seconds = timeframe_seconds
        self.look_back = look_back

        # Create initial OHLC data
        self.open_times = TimeSeries(self)
        self.open_bids = DataSeries(self)
        self.open_asks = DataSeries(self)
        if 0 != timeframe_seconds:
            self.high_bids = DataSeries(self)
            self.low_bids = DataSeries(self)
            self.close_bids = DataSeries(self)
            self.volume = DataSeries(self)
            # self.line_colors = np.array([])

    def bars_on_tick(self, time: datetime, bar: Bar) -> None:
        self.is_new_bar = False
        while self.current + 1 < len(self.open_times.data) and time >= self.open_times.data[self.current + 1]:
            self.current += 1
            self.is_new_bar = True

        # on real time trading we have to build the bars ourselves
        # if False:
        #     self.is_new_bar = False

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


# end of file
