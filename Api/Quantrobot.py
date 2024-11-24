from datetime import datetime
from math import sqrt
from typing import List
from datetime import timedelta
from PyLogger import PyLogger
from KitaSymbol import Symbol
from ConvertUtils import ConvertUtils
from CoFu import *
from AlgoApiEnums import *


# Parent trading bot
###################################
class Quantrobot:
    # pylint: disable=<no-member>
    ###################################
    def __init__(self):
        self.max_margin = [0] * 1  # arrays because of by reference
        self.same_time_open = [0] * 1
        self.same_time_open_date_time = datetime.min
        self.same_time_open_count = 0
        self.max_balance = [0] * 1
        self.max_balance_drawdown_value = [0] * 1
        self.max_balance_drawdown_time = datetime.min
        self.max_balance_drawdown_count = 0
        self.max_equity = [0] * 1
        self.max_equity_drawdown_value = [0] * 1
        self.max_equity_drawdown_time = datetime.min
        self.max_equity_drawdown_count = 0
        self.current_volume = 0
        self.initial_volume = 0
        self.open_duration_count: int = [0] * 1  # arrays because of by reference
        self.min_open_duration: timedelta = [timedelta.max] * 1
        self.avg_open_duration_sum: timedelta = [0] * 1
        self.max_open_duration: timedelta = [timedelta.min] * 1
        pass

    ###################################
    def on_start(self):
        self.logger = PyLogger(self)
        header = (
            "\nNumber"
            + ",net_profit"
            + ",Balance"
            + ",Symbol"
            + ",Mode"
            + ",Volume"
            # + ",Swap"
            + ",OpenDate"
            + ",OpenTime"
            + ",CloseDate"
            + ",CloseTime"
            + ",OpenPrice"
            + ",ClosePrice"
            + ",TradeMargin"
            # + ",MaxEquityDrawdown"
        )

        self.log_mode = LoggerConstants.self_made
        self.open_logfile(  # pylint: disable=no-member
            self.logger, self.version.split(" ")[0] + ".csv", self.log_mode, header
        )
        self.log_flush()

        self.max_equity[0] = self.Account.balance
        self.max_equity_drawdown_value[0] = 0

        self.loaded_robot.on_start(
            self, self.TradeDirection in [TradeDirection.mode1, TradeDirection.long]
        )

    ###################################
    def on_tick(self):
        # check spread
        is_spread = True
        if (
            self.symbol.spread < 0
            or self.symbol.spread
            > 2 * self.market_values.avg_spread * self.symbol.tick_size
        ):
            is_spread = False
        self.is_trading_allowed = is_spread

        # call bot's on_tick
        self.loaded_robot.on_tick(self)

        # do max/min calcs
        self.max(self.max_margin, self.Account.margin)
        if self.max(self.same_time_open, len(self.positions)):
            self.same_time_open_date_time = self.time
            self.same_time_open_count = len(self.history)

        self.max(self.max_balance, self.Account.balance)
        if self.max(
            self.max_balance_drawdown_value, self.max_balance[0] - self.Account.balance
        ):
            self.max_balance_drawdown_time = self.time
            self.max_balance_drawdown_count = len(self.history)

        self.max(self.max_equity, self.Account.equity)
        if self.max(
            self.max_equity_drawdown_value, self.max_equity[0] - self.Account.equity
        ):
            self.max_equity_drawdown_time = self.time
            self.max_equity_drawdown_count = len(self.history)
        pass

    ###################################
    def on_stop(self):
        # calc performance numbers
        min_duration = timedelta.max
        avg_duration_sum = 0
        max_duration = timedelta.min
        duration_count = 0
        max_invest_counter = [0] * 1
        # invest_count_histo = None
        avg_duration_sum += self.avg_open_duration_sum[0]
        duration_count += self.open_duration_count[0]
        min_duration = min(self.min_open_duration[0], min_duration)
        max_duration = max(self.max_open_duration[0], max_duration)
        self.loaded_robot.on_stop(self)
        #self.max(self.max_invest_count[0], self.max_invest_count)

        # if direction == TradeDirection.long == self.loaded_robot.longShorts[0].is_long:
        #     invest_count_histo = self.loaded_robot.longShorts[0].investCountHisto

        # if len(self.loaded_robot.longShorts) >= 2:
        #     if direction == TradeDirection.long == self.loaded_robot.longShorts[1].is_long:
        #         invest_count_histo = self.loaded_robot.longShorts[1].investCountHisto

        winning_trades = len([x for x in self.history if x.net_profit >= 0])
        loosing_trades = len([x for x in self.history if x.net_profit < 0])
        net_profit = sum(x.net_profit for x in self.history)
        trading_days = (  # 365 - 2*52 = 261 - 9 holidays = 252
            (self.time - self.initial_time).days / 365.0 * 252.0
        )
        if 0 == trading_days:
            annual_profit = 0
        else:
            annual_profit = net_profit / (trading_days / 252.0)
        total_trades = winning_trades + loosing_trades
        annual_profit_percent = (
            0
            if total_trades == 0
            else 100.0 * annual_profit / self.initial_account_balance
        )
        loss = sum(x.net_profit for x in self.history if x.net_profit < 0)
        profit = sum(x.net_profit for x in self.history if x.net_profit >= 0)
        profit_factor = 0 if loosing_trades == 0 else abs(profit / loss)
        max_current_equity_dd_percent = (
            100 * self.max_equity_drawdown_value[0] / self.max_equity[0]
        )
        max_start_equity_dd_percent = (
            100 * self.max_equity_drawdown_value[0] / self.initial_account_balance
        )
        calmar = (
            0
            if self.max_equity_drawdown_value[0] == 0
            else annual_profit / self.max_equity_drawdown_value[0]
        )
        winning_ratio_percent = (
            0 if total_trades == 0 else 100.0 * winning_trades / total_trades
        )

        if 0 == trading_days:
            trades_per_month = 0
        else:
            trades_per_month = total_trades / (trading_days / 252.0) / 12.0

        sharpe_ratio = self.sharpe_sortino(
            False, [trade.net_profit for trade in self.history]
        )
        sortino_ratio = self.sharpe_sortino(
            True, [trade.net_profit for trade in self.history]
        )

        # some proofs
        percent_sharpe_ratio = self.sharpe_sortino(
            False,
            [trade.net_profit / self.initial_account_balance for trade in self.history],
        )

        vals = [trade.net_profit for trade in self.history]
        average = sum(vals) / len(vals)
        sd = self.standard_deviation(False, vals)
        my_sharpe = average / sd
        # Baron
        average_daily_return = annual_profit / 252.0
        sharpe_ratio = average_daily_return / sd * sqrt(252.0)

        self.log_add_text_line("")
        self.log_add_text_line("")
        self.log_add_text_line(
            "Net Profit,"
            + ConvertUtils.double_to_string(profit + loss, 2)
            + ",,,,Long: "
            + ConvertUtils.double_to_string(
                sum(
                    x.net_profit for x in self.history if x.trade_type == TradeType.buy
                ),
                2,
            )
            + ",,,,Short:,"
            + ConvertUtils.double_to_string(
                sum(
                    x.net_profit for x in self.history if x.trade_type == TradeType.sell
                ),
                2,
            )
        )

        # self.log_add_text_line("max_margin: " + self.Account.asset + " " + ConvertUtils.double_to_string(mMaxMargin, 2))
        # self.log_add_text_line("max_same_time_open: " + str(mSameTimeOpen)
        # + ", @ " + mSameTimeOpenDateTime.strftime("%d.%m.%Y %H:%M:%S")
        # + ", Count# " + str(mSameTimeOpenCount))
        self.log_add_text_line(
            "Max Balance Drawdown Value: "
            + self.Account.asset
            + " "
            + ConvertUtils.double_to_string(self.max_balance_drawdown_value[0], 2)
            + "; @ "
            + self.max_balance_drawdown_time.strftime("%d.%m.%Y %H:%M:%S")
            + "; Count# "
            + str(self.max_balance_drawdown_count)
        )

        self.log_add_text_line(
            "Max Balance Drawdown%: "
            + (
                "NaN"
                if self.max_balance[0] == 0
                else ConvertUtils.double_to_string(
                    100 * self.max_balance_drawdown_value[0] / self.max_balance[0], 2
                )
            )
        )

        self.log_add_text_line(
            "Max Equity Drawdown Value: "
            + self.Account.asset
            + " "
            + ConvertUtils.double_to_string(self.max_equity_drawdown_value[0], 2)
            + "; @ "
            + self.max_equity_drawdown_time.strftime("%d.%m.%Y %H:%M:%S")
            + "; Count# "
            + str(self.max_equity_drawdown_count)
        )

        self.log_add_text_line(
            "Max Current Equity Drawdown %: "
            + ConvertUtils.double_to_string(max_current_equity_dd_percent, 2)
        )

        self.log_add_text_line(
            "Max start Equity Drawdown %: "
            + ConvertUtils.double_to_string(max_start_equity_dd_percent, 2)
        )

        self.log_add_text_line(
            "Profit Factor: "
            + (
                "-"
                if loosing_trades == 0
                else ConvertUtils.double_to_string(profit_factor, 2)
            )
        )

        self.log_add_text_line(
            "Sharpe Ratio: " + ConvertUtils.double_to_string(sharpe_ratio, 2)
        )
        self.log_add_text_line(
            "Sortino Ratio: " + ConvertUtils.double_to_string(sortino_ratio, 2)
        )

        self.log_add_text_line(
            "Calmar Ratio: " + ConvertUtils.double_to_string(calmar, 2)
        )
        self.log_add_text_line(
            "Winning Ratio: " + ConvertUtils.double_to_string(winning_ratio_percent, 2)
        )

        self.log_add_text_line(
            "Trades Per Month: " + ConvertUtils.double_to_string(trades_per_month, 2)
        )

        self.log_add_text_line(
            "Average Annual Profit Percent: "
            + ConvertUtils.double_to_string(annual_profit_percent, 2)
        )

        # if avg_open_duration_sum != 0:
        #     self.log_add_text_line(
        #         "Min / Avg / Max Tradeopen Duration (Day.Hour.Min.sec): "
        #         + str(min_duration)
        #         + " / "
        #         + str(avg_open_duration_sum / avg_open_duration_sum)
        #         + " / "
        #         + str(self.max_duration)
        #     )
        self.log_add_text_line("Max Repurchase: " + str(max_invest_counter[0]))
        # histo_rest_sum = 0.0
        # if investCountHisto is not None:
        #     for i in range(len(investCountHisto) - 1, 0, -1):
        #         if investCountHisto[i] != 0:
        #             self.log_add_text_line("Invest " + str(i) + ": " + str(investCountHisto[i]))
        #             if i > 1:
        #                 histoRestSum += investCountHisto[i]
        #     if histoRestSum != 0:
        #         self.log_add_text_line("histo_rest_quotient: " + ConvertUtils.double_to_string(m_histo_rest_quotient = investCountHisto[1] / histoRestSum,
        self.log_close()

    def calculate_reward(self, tradingClass):
        return self.loaded_robot.get_tick_fitness(tradingClass)

    # pylint: disable=<no-member>


# end of file