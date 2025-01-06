from datetime import datetime
from Api.Bar import Bar
from Api.TimeSeries import TimeSeries
from Api.DataSeries import DataSeries


class Bars:
    # bars are not indexed; only time and data series are indexed
    # No bars.Last().open_time; Use bars.open_times.Last() instead
    # So no: def __getitem__(self, index: int) -> Bar: # Returns a bar based on its index#
    # and no: @property
    # def last_bar(self) -> Bar: # Gets the last bar in the chart.#

    # Members
    # region
    symbol_name: str  # Gets the symbol name.#
    timeframe_seconds: int  # Get the timeframe in seconds.#
    look_back: int  # Gets the look back period.#
    open_times: TimeSeries  # Gets the open bar time data.#
    open_prices: DataSeries  # Gets the Open price bars data.#
    high_prices: DataSeries  # Gets the High price bars data.#
    low_prices: DataSeries  # Gets the Low price bars data.#
    close_prices: DataSeries  # Gets the Close price bars data.#
    volume: DataSeries  # Gets the tick volumes data.#
    open_asks: DataSeries  # The ask value at open time (open_prices are bids)
    is_new_bar: bool = False
    chart_time_array = []

    @property
    def count(self) -> int:  # Gets the number of bars.#
        return len(self.open_times.data)

    # endregion

    def __init__(self, symbol_name: str, timeframe_seconds: int, look_back: int):
        self.symbol_name = symbol_name
        self.timeframe_seconds = timeframe_seconds
        self.look_back = look_back

        # Create initial OHLC data
        self.open_times = TimeSeries()
        self.open_prices = DataSeries()
        self.open_asks = DataSeries()
        if 0 != timeframe_seconds:
            self.high_prices = DataSeries()
            self.low_prices = DataSeries()
            self.close_prices = DataSeries()
            self.volume = DataSeries()
            # self.line_colors = np.array([])

    # forward declarations
    def is_new_bar_get(self, seconds: int, time: datetime, prevTime: datetime) -> bool: ...

    def on_tick(self, bar: Bar) -> None:
        self.is_new_bar = False

        # do we have to build a new bar ?
        if (
            0 == self.open_times.count  # on init
            or 0 == self.timeframe_seconds  # tick data rate
            or self.is_new_bar_get(self.timeframe_seconds, bar.open_time, self.open_times.data[-1])  # new bar ?
        ):
            self.open_times.data.append(bar.open_time)
            self.open_prices.data.append(bar.open_price)
            self.open_asks.data.append(bar.open_ask)
            if 0 != self.timeframe_seconds:
                self.high_prices.data.append(bar.open_price)
                self.low_prices.data.append(bar.open_price)
                self.close_prices.data.append(bar.open_price)
                self.volume.data.append(0)

            self.is_new_bar = True
        else:
            self.high_prices.data[-1] = max(self.high_prices.data[-1], bar.high_price)
            self.low_prices.data[-1] = min(self.low_prices.data[-1], bar.low_price)
            self.close_prices.data[-1] = bar.close_price
            self.volume.data[-1] += 1 if 0 == bar.volume else bar.volume

        # self.open_prices.update_indicators(self.open_times.count - 1, self.is_new_bar)
        # self.high_prices.update_indicators(self.open_times.count - 1, self.is_new_bar)
        # self.low_prices.update_indicators(self.open_times.count - 1, self.is_new_bar)
        # self.close_prices.update_indicators(self.open_times.count - 1, self.is_new_bar)
        # self.volume.update_indicators(self.open_times.count - 1, self.is_new_bar)
        # self.open_asks.update_indicators(self.open_times.count - 1, self.is_new_bar)

    """
    @property
    def median_prices(self) -> DataSeries:
        # Gets the Median prices data (High + Low) / 2.#
        ...

    @property
    def typical_prices(self) -> DataSeries:
        # Gets the Typical prices data (High + Low + Close) / 2.#
        ...

    @property
    def weighted_prices(self) -> DataSeries:
        # Gets the Weighted prices data (High + Low + 2 * Close) / 4.#
        ...

    def load_more_history(self) -> int:
        # Loads more historical bars. Method returns the number of loaded bars that were added to the beginning of the collection.#
        ...

    def load_more_history_async(self) -> None:
        # Loads more historical bars asynchronously.#
        ...

    def load_more_history_async_callback(self, callback: Callable[[bars_history_loaded_event_args], None]) -> None:
        #Loads more historical bars asynchronously with a callback.#
        ...

    # Events
    def history_loaded_event(self, callback: Callable[[bars_history_loaded_event_args], None]) -> None:
        #Occurs when more history is loaded due to chart scroll on the left or due to API call.#
        ...

    def reloaded_event(self, callback: Callable[[bars_history_loaded_event_args], None]) -> None:
        #Occurs when bars are refreshed due to reconnect.#
        ...

    def tick_event(self, callback: Callable[[bars_tick_event_args], None]) -> None:
        #Occurs when a new tick arrives.#
        ...

    def bar_opened_event(self, callback: Callable[[bar_opened_event_args], None]) -> None:
        #Occurs when the last bar is closed and a new bar is opened.#
        ...

    def bar_closed_event(self, callback: Callable[[bar_closed_event_args], None]) -> None:
        #Occurs when a new bar is opened; the event is called for the previous (closed) bar.#
        ...
    """


# end of file
