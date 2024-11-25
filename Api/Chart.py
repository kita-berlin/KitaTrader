import numpy as np
from bokeh.plotting import figure
from bokeh.models import (
    ColumnDataSource,
    FixedTicker,
)
from datetime import datetime
from ChartArea import ChartArea
from KitaSymbol import Symbol
from Bars import Bars
from AlgoApiEnums import ChartIconType
from Settings import BinSettings


################################################
class Chart(ChartArea):
    def __init__(
        self, symbol: Symbol, bars: Bars, bin_settings: BinSettings
    ):
        self.chart_bars = bars
        self.symbol = symbol
        self.bin_settings = bin_settings

        self.x_axis_step = 8
        self.drawings_dictionary = {}

        # no plot if not visible
        if bin_settings.is_visual_mode:
            # Create a new plot
            self.ohlc_plot = figure(
                height=400,
                width=1200,
                title=self.symbol.name if None != symbol else "",
            )

            # Remove horizontal grid lines
            self.ohlc_plot.ygrid.grid_line_color = None

            # Generate sequential x values
            self.x = np.arange(self.bin_settings.bars_in_chart)

            # Compute x positions for horizontal lines
            self.x_open = self.x - 0.4
            self.x_close = self.x + 0.4

            self.source = ColumnDataSource(
                dict(
                    x=self.x,
                    x_open=self.x_open,
                    x_close=self.x_close,
                    line_colors=bars.line_colors[-self.bin_settings.bars_in_chart :],
                    times=bars.open_times.data[-self.bin_settings.bars_in_chart :],
                    opens=bars.open_prices.data[-self.bin_settings.bars_in_chart :],
                    highs=bars.high_prices.data[-self.bin_settings.bars_in_chart :],
                    lows=bars.low_prices.data[-self.bin_settings.bars_in_chart :],
                    closes=bars.close_prices.data[-self.bin_settings.bars_in_chart :],
                )
            )

            # Draw vertical lines between low and high with conditional color
            self.ohlc_plot.segment(
                x0="x",
                y0="highs",
                x1="x",
                y1="lows",
                source=self.source,
                line_color="lineColors",
                line_width=3,
            )

            # Add horizontal lines for open...
            self.ohlc_plot.segment(
                x0="x_open",
                y0="opens",
                x1="x",
                y1="opens",
                source=self.source,
                line_color="lineColors",
                line_width=3,
            )

            # ...and close
            self.ohlc_plot.segment(
                x0="x_close",
                y0="closes",
                x1="x",
                y1="closes",
                source=self.source,
                line_color="lineColors",
                line_width=3,
            )

            # Init the x-axis ticks and labels
            if bars.count > self.bin_settings.bars_in_chart:
                self.x_axis_labels = []
                step = self.bin_settings.bars_in_chart // self.x_axis_step
                for i in range(0, self.bin_settings.bars_in_chart, step):
                    for j in range(i, i + step, 1):
                        if (
                            0
                            == bars.open_times[j].timestamp()
                            % self.chart_bars.default_timeframe_seconds
                        ):
                            self.x_axis_labels.append(j)
                            break

                self.ohlc_plot.xaxis.ticker = FixedTicker(ticks=self.x_axis_labels)

                self.ohlc_plot.xaxis.major_label_overrides = {
                    tick: Bars.open_times[tick].strftime("%d-%m-%Y %H:%M")
                    for tick in self.x_axis_labels
                }
        pass

    ###################################
    def get_xfrom_datetime(self, time: datetime) -> int:
        closest_index = -1
        min_difference = float("inf")

        for i, dt in enumerate(self.chart_bars.chart_time_array):
            difference = abs((dt - time).total_seconds())
            if difference < min_difference:
                min_difference = difference
                closest_index = i

        return closest_index

    ###################################
    def update_chart_drawings(self):
        # self.drawings_dictionary[name] = (scatter, x_value, yValue, source, marker, color)
        del_keys = []
        for key, value in self.drawings_dictionary.items():
            new_x = value[3].data["x"][0] - 1
            if new_x < 0:
                del_keys.append(key)
                self.ohlc_plot.renderers.remove(value[0])
            else:
                value[3].data = {"x": [new_x], "y": [value[3].data["y"][0]]}

        for key in del_keys:
            del self.drawings_dictionary[key]

    ###################################
    def draw_icon(
        self,
        name: str,
        iconType: ChartIconType,
        time: datetime,
        yValue: float,
        color: str,
    ):
        if not self.bin_settings.is_visual_mode:
            return

        marker = None
        if ChartIconType.UpArrow == iconType:
            marker = "triangle"
        elif ChartIconType.DownArrow == iconType:
            marker = "triangle-down"  # type

        x_value = self.get_xfrom_datetime(time)
        data = {"x": [x_value], "y": [yValue]}
        source = ColumnDataSource(data=data)

        scatter = self.ohlc_plot.scatter(
            source=source,
            marker=marker,  # type
            size=10,
            fill_color=color,  # color
        )

        self.drawings_dictionary[name] = (
            scatter,
            x_value,
            yValue,
            source,
            marker,
            color,
        )

    ################################################
    # @property
    # def indicator_areas(self) -> List['indicator_area']:
    #     pass

    # @property
    # def display_settings(self) -> 'chart_display_settings':
    #     pass

    # @property
    # def color_settings(self) -> 'chart_color_settings':
    #     pass

    # @property
    # def ChartType(self) -> ChartType:
    #     pass

    # @ChartType.setter
    # def ChartType(self, value: ChartType):
    #     pass

    @property
    def zoom_level(self) -> int:
        return 0
        pass

    @zoom_level.setter
    def zoom_level(self, value: int):
        return 0
        pass

    @property
    def first_visible_bar_index(self) -> int:
        return 0
        pass

    @property
    def last_visible_bar_index(self) -> int:
        return 0
        pass

    @property
    def max_visible_bars(self) -> int:
        return 0
        pass

    @property
    def bars_total(self) -> int:
        return 0
        pass

    chart_bars: Bars

    # @property
    # def Timeframe(self) -> Timeframe:
    #     pass

    @property
    def is_scrolling_enabled(self) -> bool:
        return False
        pass

    @is_scrolling_enabled.setter
    def is_scrolling_enabled(self, value: bool) -> bool:
        return False
        pass

    @property
    def is_active(self) -> bool:
        return False
        pass

    @property
    def is_visible(self) -> bool:
        return False
        pass

    def scroll_x_by(self, bars: int):
        pass

    def scroll_x_to(self, barIndex: int):
        pass

    # def scroll_x_to(self, time: datetime):
    #     pass

    def set_bar_color(self, barIndex: int, str: str):
        pass

    def set_bar_fill_color(self, barIndex: int, str: str):
        pass

    def set_bar_outline_color(self, barIndex: int, str: str):
        pass

    def set_tick_volume_color(self, barIndex: int, str: str):
        pass

    def reset_bar_color(self, barIndex: int):
        pass

    def reset_bar_colors(self):
        pass

    def reset_tick_volume_color(self, barIndex: int):
        pass

    def reset_tick_volume_colors(self):
        pass

    # def add_hotkey(self, hotkeyHandler, key, modifiers =None) -> bool:
    #     pass

    # def try_change_time_frame(self, timeFrame: Timeframe) -> bool:
    #     pass

    # def try_change_time_frame_and_symbol(self, timeFrame: Timeframe, symbolName: str) -> bool:
    #     pass

    # def take_chartshot(self) -> Union[bytearray, None]:
    #     pass
