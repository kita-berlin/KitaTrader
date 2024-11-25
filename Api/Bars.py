import numpy as np
from DataSeries import DataSeries
from TimeSeries import TimeSeries


class Bars:
    # bars are not indexed; only time and data series are indexed
    # No bars.Last().open_time; Use bars.open_times.Last() instead
    # So no: def __getitem__(self, index: int) -> Bar: # Returns a bar based on its index#

    # and no: @property
    # def last_bar(self) -> Bar: # Gets the last bar in the chart.#

    # Members
    # region
    @property
    def count(self) -> int:  # Gets the number of bars.#
        return len(self.open_times.data)

    default_timeframe_seconds: int  # Get the timeframe in seconds.#
    symbol_name: str  # Gets the symbol name.#
    open_prices: DataSeries  # Gets the Open price bars data.#
    high_prices: DataSeries  # Gets the High price bars data.#
    low_prices: DataSeries  # Gets the Low price bars data.#
    close_prices: DataSeries  # Gets the Close price bars data.#
    tick_volumes: DataSeries  # Gets the tick volumes data.#
    open_asks: DataSeries  # The ask value at open time (open_prices are bids)
    open_times: TimeSeries  # Gets the open bar time data.#
    is_new_bar: bool = False
    chart_time_array = []
    # endregion

    def __init__(self, trading_class, timeframeSeconds: int, symbolName: str):
        self.trading_class = trading_class
        self.default_timeframe_seconds = timeframeSeconds
        self.symbol_name = symbolName

        # Create initial OHLC data for drawing
        self.open_times = TimeSeries()
        self.open_prices = DataSeries()
        self.high_prices = DataSeries()
        self.low_prices = DataSeries()
        self.close_prices = DataSeries()
        self.tick_volumes = DataSeries()
        self.open_asks = DataSeries()
        self.line_colors = np.array([])

    pass

    ######################################
    def update_bar(self, quote) -> None:
        self.is_new_bar = False

        # do we have to build a new bar ?
        epoc_dt = quote.time.timestamp() // 60
        tf_minutes = self.default_timeframe_seconds // 60
        tf_modulo = epoc_dt % tf_minutes
        if 0 == self.open_times.count or self.trading_class.is_new_bar(
            self.default_timeframe_seconds, quote.time, self.open_times.data[-1]
        ):
            self.open_times.data = np.append(self.open_times.data, quote.time)
            self.open_prices.data = np.append(self.open_prices.data, quote.open)
            self.high_prices.data = np.append(self.high_prices.data, quote.open)
            self.low_prices.data = np.append(self.low_prices.data, quote.open)
            self.close_prices.data = np.append(self.close_prices.data, quote.open)
            self.tick_volumes.data = np.append(self.tick_volumes.data, 0)
            self.open_asks.data = np.append(self.open_asks.data, quote.open_ask)
            self.line_colors = np.append(self.line_colors, "green")
            self.is_new_bar = True
        else:
            self.high_prices.data[-1] = max(self.high_prices.data[-1], quote.High)
            self.low_prices.data[-1] = min(self.low_prices.data[-1], quote.Low)
            self.close_prices.data[-1] = quote.close
            self.tick_volumes.data[-1] += (
                1 if 0 == self.tick_volumes.data[-1] else self.tick_volumes.data[-1]
            )
            self.line_colors[-1] = (
                "green"
                if self.close_prices.data[-1] > self.open_prices.data[-1]
                else "red"
            )

        self.open_prices.update_indicators(self.open_times.count - 1, self.is_new_bar)
        self.high_prices.update_indicators(self.open_times.count - 1, self.is_new_bar)
        self.low_prices.update_indicators(self.open_times.count - 1, self.is_new_bar)
        self.close_prices.update_indicators(self.open_times.count - 1, self.is_new_bar)
        self.tick_volumes.update_indicators(self.open_times.count - 1, self.is_new_bar)
        self.open_asks.update_indicators(self.open_times.count - 1, self.is_new_bar)

    pass
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