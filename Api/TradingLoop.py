import numpy as np
from datetime import datetime, timedelta, timezone
from bokeh.models import FixedTicker
from Chart import Chart
from Settings import *
from MarketData import *
from CoFu import *
from AlgoApiEnums import *


class TradingLoop:
    def __init__(self):
        pass

    ###################################
    def update_chart_text_and_bars(self):
        self.BalanceValue.text = "{:.2f}".format(self.Account.balance)
        self.EquityValue.text = "{:.2f}".format(self.Account.equity)
        self.DatetimeValue.text = self.time.strftime("%d-%m-%Y %H:%M:%S")
        self.MaxEqDdValue.text = "{:.2f}".format(self.MaxEquityDrawdownValue[0])

        if self.bin_settings.is_visual_mode:
            if len(self.chart.x) != self.bin_settings.bars_in_chart:
                self.chart.x = np.arange(self.bin_settings.bars_in_chart)
                self.chart.x_open = self.chart.x - 0.4
                self.chart.x_close = self.chart.x + 0.4
            pass

            self.bars.ChartTimeArray = self.bars.OpenTimes.data[
                -self.bin_settings.bars_in_chart :
            ]
            self.chart.source.data = {
                "x": self.chart.x,
                "x_open": self.chart.x_open,
                "x_close": self.chart.x_close,
                "lineColors": self.bars.LineColors[
                    -self.bin_settings.bars_in_chart :
                ],
                "times": self.bars.ChartTimeArray,
                "opens": self.bars.OpenPrices.data[
                    -self.bin_settings.bars_in_chart :
                ],
                "highs": self.bars.HighPrices.data[
                    -self.bin_settings.bars_in_chart :
                ],
                "lows": self.bars.LowPrices.data[-self.bin_settings.bars_in_chart :],
                "closes": self.bars.ClosePrices.data[
                    -self.bin_settings.bars_in_chart :
                ],
            }
        pass

    ###################################
    def pre_start(self):
        # Init member variables
        # region
        self.initial_time = self.time = self.PrevTime = self.bin_settings.start_dt
        self.initial_account_balance = self.Account.equity = self.Account.balance = (
            self.bin_settings.init_balance
        )
        self.TradeDirection = self.bin_settings.TradeDirection

        self.running_mode = (
            RunningMode.visual_backtesting
            if self.bin_settings.is_visual_mode
            else RunningMode.silent_backtesting
        )
        self.is_stop = False
        self.bars = None
        # endregion

        # Init default symbol
        self.symbol = self.get_symbol(self.bin_settings.default_symbol_name)

        # Init default bars (needed for chart if visible)
        if self.bin_settings.bars_in_chart > 0:
            self.bars = self.market_data.get_bars(
                self.bin_settings.default_timeframe_seconds, self.symbol.name
            )

        # Höhere Entropiewerte bedeuten, dass die Datenquelle weniger vorhersehbar
        # und zufälliger ist. Umgekehrt bedeuten niedrigere Entropiewerte,
        # dass die Datenquelle vorhersehbarer und weniger zufällig ist.

        """
        # Generate a random price series
        price_series = np.randoself.normal(1, 0.2, 100000)

        # Calculate the probability distribution of price changes
        price_changes = np.diff(price_series) / price_series[:-1]
        p, bins = np.histogram(price_changes, bins="auto", density=True)

        # Calculate Shannon entropy
        randomShannonEntropy = entropy(p)

        # Calculate the probability distribution of price changes
        barsPriceChanges = (
            np.diff(self.bars.ClosePrices.data) / self.bars.ClosePrices.data[:-1]
        )
        barsP, bins = np.histogram(barsPriceChanges, bins="auto", density=True)

        # Calculate Shannon entropy
        barsShannonEntropy = entropy(barsP)
        """

        self.chart = Chart(
            self.symbol,
            self.bars,
            self.bin_settings,
        )

        self.time = self.initial_time = self.symbol.time
        pass

    ###################################
    def start(self):
        # call bot
        self.on_start()

    #####################################
    def Tick(self):
        # update quote, bars, Indicators
        # of 1st tick must update all bars and Indicators which have been inized in on_start()
        for symbol in self.symbol_list:
            error = symbol.on_tick()
            if "" != error or self.symbol_list[0].time > self.bin_settings.end_dt:
                return True

        self.time = self.symbol_list[0].time

        if None != self.bars:
            # Update the chart if visible and new bar
            if self.bin_settings.is_visual_mode:
                if 1000 != self.bin_settings.speed:
                    if self.bars.IsNewBar:
                        # x axis
                        # region
                        for i in range(len(self.chart.x_axis_labels)):
                            self.chart.x_axis_labels[i] -= 1

                        if self.chart.x_axis_labels[0] < 0:
                            self.chart.x_axis_labels.pop(0)

                        if (
                            self.bin_settings.bars_in_chart
                            - self.chart.x_axis_labels[-1]
                            > self.bin_settings.bars_in_chart
                            // self.chart.x_axis_step
                            and 0
                            == self.bars.OpenTimes.data[
                                -self.bin_settings.bars_in_chart :
                            ][-1].timestamp()
                            % self.bars.default_timeframe_seconds
                        ):
                            self.chart.x_axis_labels.append(
                                self.bin_settings.bars_in_chart - 1
                            )

                        self.chart.OhlcPlot.xaxis.ticker = FixedTicker(
                            ticks=self.chart.x_axis_labels
                        )

                        self.chart.OhlcPlot.xaxis.major_label_overrides = {
                            tick: self.bars.OpenTimes.data[
                                -self.bin_settings.bars_in_chart :
                            ][tick].strftime("%d-%m-%Y %H:%M")
                            for tick in self.chart.x_axis_labels
                        }
                        # endregion

                        self.chart.UpdateChartDrawings()

        ########################################
        # Update Account
        if len(self.positions) >= 1:
            if Platform.mt5_live == self.bin_settings.Platform:
                import MetaTrader5 as mt5

                account_info = mt5.account_info()
                self.Account.balance = account_info.balance
                self.Account.equity = account_info.equity
                self.Account.margin = account_info.margin
                self.Account.FreeMargin = account_info.margin_free
                self.Account.MarginLevel = account_info.margin_level
                self.Account.unrealized_net_profit = account_info.profit
            else:
                open_positions_profit = 0
                for x in self.positions:
                    open_positions_profit += (
                        (x.current_price - x.entry_price)
                        * (1 if x.trade_type == TradeType.buy else -1)
                        * x.volume_in_units
                    )
                    self.Account.unrealized_net_profit += open_positions_profit
                    x.max_drawdown = min(x.max_drawdown, open_positions_profit)

                self.Account.equity = self.Account.balance + open_positions_profit
            pass

        # call bot
        self.on_tick()

        return False

    ###########################################
    def Stop(self):
        # call bot
        self.OnStop()


# end of file