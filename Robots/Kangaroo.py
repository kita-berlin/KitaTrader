import numpy as np
import pandas as pd
from math import sqrt
from typing import List
from datetime import timedelta
from IIndicators import Indicators
from PyLogger import PyLogger
from HedgePosition import HedgePosition
from IRobot import IRobot
from AlgoApiEnums import *
from Api.CoFu import *
from Constants import *

# import talib
# from talib import MA_Type


class Kangaroo(IRobot):
    # Members
    # region
    sqrt252: float = sqrt(252)
    # endregion

    def __init__(self):
        # History
        # region
        self.version = "Kangaroo V1.0"
        # V1.0     14.02.23    HMz created
        # endregion

        # Parameter
        # region
        self.rebuy_1st_percent = 1.0
        self.rebuy_percent = 0.1
        self.take_profit_percent = 0.1
        self.volume = 1000

    # endregion
    pass

    ###################################
    def on_start(self, is_long):

        # Members; We do declaration here so members will be reinized by 2nd++ on_start()
        # region
        self.is_long = is_long
        self.current_volume = self.initial_volume = self.volume
        self.hedge_positions: List[HedgePosition] = []
        self.max_invest_count: List[int] = [0] * 1
        self.cluster_count: int = 0
        self.avg_price: float = 0
        self.invest_count: int = 0
        self.current_volume: float = 0
        self.cluster_profit: float = 0
        self.daily_revenue: List[float] = []
        self.prev_revenue: float = 0
        self.sharpe_ratio: float = 0
        self.sortino_ratio: float = 0
        self.calmar: float = 0
        self.is_train: bool = False

        """ example how to use indicators
        self.time_period = 14
        self.indi_bars = self.market_data.get_bars(SEC_PER_HOUR, self.symbol.name)
        
        self.sma = indicators.moving_average(
            source =self.indi_bars.close_prices,
            periods =self.time_period,
            ma_type =MovingAverageType.Simple,
        )

        self.sd = indicators.standard_deviation(
            source =self.indi_bars.close_prices,
            periods =self.time_period,
            ma_type =MovingAverageType.Simple,
        )

        self.bb_indi:indicators.bollinger_bands = indicators.bollinger_bands(
            source =self.indi_bars.close_prices,
            periods =self.time_period,
            standard_deviations =2,
            ma_type =MovingAverageType.Simple,
            shift =0,
        )
        """
        # endregion

        if not self.is_train:
            print(
                "Time; Direction; Profit; max_equity_draw_down; cluster_count; invest_count; calmar; Rebuy1st%; Rebuy%; take_profit%"
            )

    ###################################
    def on_tick(self):
        """example how to use own indicators and ta-lib
        ta_sma = talib.SMA(
            self.indi_bars.close_prices.data[-self.time_period :], timeperiod =self.time_period
        )[-1]
        my_sma = self.Sma.Result.Last(0)

        ta_sd = talib.STDDEV(
            self.indi_bars.close_prices.data[-self.time_period :], timeperiod =self.time_period
        )[-1]
        my_sd = self.Sd.Result.Last(0)

        taUpperArray, taMiddleArray, ta_lower_array = talib.BBANDS(
            self.indi_bars.close_prices.data[-self.time_period :],
            timeperiod =self.time_period,
            nbdevup =2,
            nbdevdn =2,
            matype =MA_Type.SMA
        )
        ta_upper = taUpperArray[-1]
        ta_middle = taMiddleArray[-1]
        ta_lower = taLowerArray[-1]

        my_upper = self.bb_indi.Top.Last(0)
        my_middle = self.bb_indi.Main.Last(0)
        my_lower = self.bb_indi.Bottoself.Last(0)
        """

        current_open = self.symbol.Ask if self.is_long else self.symbol.Bid
        current_close = self.symbol.Bid if self.is_long else self.symbol.Ask

        if 0 == self.invest_count:
            self.cluster_profit = 0
            self.current_volume = self.initial_volume
        pass

        if self.invest_count >= 1:
            last_position = self.hedge_positions[-1]
            self.cluster_profit = self.current_volume = 0
            cluster_price_by_volume_sum = 0

            for pos in self.hedge_positions:
                self.cluster_profit += pos.profit
                cluster_price_by_volume_sum += (
                    pos.main_position.entry_price * pos.main_position.volume_in_units
                )
                self.current_volume += pos.main_position.volume_in_units

            self.avg_price = (
                cluster_price_by_volume_sum / self.current_volume
                + last_position.freeze_price_offset
            )

            current_repurchase_price = self.sub_long(
                self.is_long,
                last_position.freeze_corrected_entry_price,
                last_position.freeze_corrected_entry_price
                * (
                    self.rebuy_1st_percent
                    if self.invest_count < 2
                    else self.rebuy_percent
                )
                / 100,
            )

            tp_value = current_close * self.take_profit_percent / 100
            tp_price = self.add_long(self.is_long, self.avg_price, tp_value)
            tp_points = self.i_price(tp_value, self.symbol.tick_size)

            # initial_target_cash = self.parent_bot.mBot.calc_points_and_volume_2money(self.parent_bot.bot_symbol, tp_points, self.parent_bot.initial_volume)
            target_cash = self.calc_points_and_volume_2money(
                self.symbol, tp_points, self.current_volume
            )
        pass

        # Take Profit ?
        is_just_closed = False
        if self.is_trading_allowed:
            if self.invest_count > 0:
                # check profit instead of price because of swaps etc.
                if self.cluster_profit > target_cash:
                    invest_count = self.invest_count
                    self.loaded_robot.close_all_open_positions(
                        self
                    )  # close all open trades
                    # "Time; Profit; max_equity_draw_down; cluster_count; invest_count; calmar; Rebuy1st%; Rebuy%; take_profit%"
                    if not self.is_train:
                        print(
                            self.time.strftime("%d-%m-%Y %H:%M:%S; ")
                            + ("Long" if self.is_long else "Short")
                            + "; {:.2f}".format(
                                self.Account.balance - self.initial_account_balance
                            )
                            + "; {:.2f}".format(self.max_equity_drawdown_value[0])
                            + "; {}".format(self.cluster_count)
                            + "; {}".format(self.invest_count)
                            + "; {:.2f}".format(self.calmar)
                        )

                    if self.trade_direction == TradeDirection.Mode1:
                        self.is_long = not self.is_long  # flip direction
                    is_just_closed = True
        pass

        # buy ?
        if self.is_trading_allowed and not is_just_closed:
            is_reinvest = False
            volume_to_add = self.initial_volume

            if 0 == self.invest_count:
                is_reinvest = True

            if self.invest_count > 0:
                if self.is_less_long(
                    self.is_long,
                    current_open,
                    current_repurchase_price,
                ):
                    is_reinvest = True

            if is_reinvest:
                # Hier sollte der Regler oder die KI greifen:
                # Mit wie viel volume_to_add soll (nach)gekauft werden und
                # wie sollen die Parameter Rebuy1stPercent, rebuy_percent
                # und take_profit_percent aussehen?
                # Das volume_to_add beeinflusst den Mischpreis (self.avg_price)
                # und zieht ihn näher zum aktuellen Preis hin
                h_pos = HedgePosition(
                    self,
                    self.symbol,
                    self.is_long,
                    self.loaded_robot.get_label(self),
                )
                h_pos.do_main_open(volume_to_add)
                self.hedge_positions.append(h_pos)
                self.invest_count += 1
                self.max(self.max_invest_count, self.invest_count)
                if not self.is_train:
                    print(
                        self.time.strftime("%d-%m-%Y %H:%M:%S; ")
                        + ("Long" if self.is_long else "Short")
                        + "; {:.2f}".format(
                            self.Account.balance - self.initial_account_balance
                        )
                        + "; {:.2f}".format(self.max_equity_drawdown_value[0])
                        + "; {}".format(self.cluster_count)
                        + "; {}".format(self.invest_count)
                        + "; {:.2f}".format(self.calmar)
                        + "; {:.2f}".format(self.rebuy_1st_percent)
                        + "; {:.2f}".format(self.rebuy_percent)
                        + "; {:.2f}".format(self.take_profit_percent)
                    )
                    pass
            else:
                pass  # for debugging

        # self.get_tick_fitness()  # calculate calmar
        pass

    ###################################
    def on_stop(self):
        print("Done")
        pass

        ###################################

    ###################################
    def get_label(self):
        return (
            f"{self.version};"
            f"{self.cluster_count}_{self.invest_count};"
            f"{int(0.5 + (self.symbol.Ask if self.is_long else self.symbol.Bid) / self.symbol.tick_size)};"
            f"{self.time};"
        )

    ###################################
    def close_all_open_positions(self):
        is_cluster = len(self.hedge_positions) >= 2
        # if isCluster:
        #     self.log_add_text("\n")

        for i in range(len(self.hedge_positions) - 1, -1, -1):
            self.hedge_positions[i].do_main_close(
                self.min_open_duration,
                self.avg_open_duration_sum,
                self.open_duration_count,
                self.max_open_duration,
            )

        # if isCluster:
        self.log_add_text("\n")

        self.cluster_count += 1
        self.hedge_positions = []
        self.invest_count = 0

    ###################################
    def get_tick_fitness(self) -> float:
        # ret_val = 0.0
        self.history  # list of closed positions
        self.positions  # list of current open positions; Count matches self.invest_count
        self.initial_account_balance  # start balance
        self.Account.balance  # start balance plus profit sum of all CLOSED positions (sum of REALIZED profit)
        self.Account.equity  # self.Account.balance plus profit sum of all OPEN positions (sum of UNREALIZED profit)
        self.cluster_count  # number of current cluster
        self.invest_count  # number of open trades within current cluster
        self.Account.margin  # sum of all open Position margins; equal to sum(x.margin for x in self.positions)
        # self.max_equity_drawdown_value[0] holds biggest difference of self.Account.balance and self.Account.equity
        self.max_equity_drawdown_value[0]

        # composed values
        history_profit = self.Account.balance - self.initial_account_balance
        # history_profit is equal to sum(x.net_profit for x in self.history)

        revenue = history_profit + self.cluster_profit
        # self.cluster_profit is equal to sum(x.net_profit for x in self.positions)

        self.daily_revenue.append(revenue - self.prev_revenue)
        # self.sharpe_ratio = self.sharpe_sortino(False, self.daily_revenue) * self.Sqrt252
        # self.sortino_ratio = self.sharpe_sortino(True, self.daily_revenue) * self.Sqrt252
        if 0 != self.max_equity_drawdown_value[0]:
            self.calmar = revenue / self.max_equity_drawdown_value[0]

        self.prev_revenue = revenue

        return self.calmar
