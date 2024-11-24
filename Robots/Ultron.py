import numpy as np
import pandas as pd
from math import sqrt
from typing import List
from datetime import timedelta
from indicators import indicators
from PyLogger import PyLogger
from HedgePosition import HedgePosition
from TradingBot import TradingBot
from AlgoApiEnums import *
from CoFu import *
from constants import *

# import talib
# from talib import MA_Type


# Single direction trading bot
###################################
class Ultron(TradingBot):
    def __init__(self):

        # Parameter
        # region
        # self.rebuy_1st_percent = 1.0
        # self.rebuy_percent = 0.1
        # self.take_profit_percent = 0.1
        # self.volume = 1000

        # endregion
        pass

    ###################################
    def on_start(self, is_long):
        self.is_long = is_long

        # Members; We do declaration here so members will be reinized by 2nd++ on_start()
        # region
        self.hedge_positions: HedgePosition = []
        self.open_duration_count: int = [0] * 1  # arrays because of by reference
        self.min_open_duration: timedelta = [timedelta.max] * 1
        self.avg_open_duration_sum: timedelta = [0] * 1
        self.max_open_duration: timedelta = [timedelta.min] * 1

        """ example how to use indicators
        self.time_period = 14
        self.indi_bars = self.market_data.get_bars(SEC_PER_HOUR, self.symbol.name)
        
        self.sma = indicators.moving_average(
            source =self.indi_bars.close_prices,
            periods =self.time_period,
            ma_type =MovingAverageType.simple,
        )

        self.sd = indicators.standard_deviation(
            source =self.indi_bars.close_prices,
            periods =self.time_period,
            ma_type =MovingAverageType.simple,
        )

        self.bb_indi:indicators.bollinger_bands = indicators.bollinger_bands(
            source =self.indi_bars.close_prices,
            periods =self.time_period,
            standard_deviations =2,
            ma_type =MovingAverageType.simple,
            shift =0,
        )
        """
        # endregion

        if not self.is_train:
            print(
                "Time; Direction; Profit; max_equity_draw_down; cluster_count; invest_count; Calmar; Rebuy1st%; Rebuy%; take_profit%"
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

        current_open = self.symbol.ask if self.is_long else self.symbol.bid
        current_close = self.symbol.bid if self.is_long else self.symbol.ask

        pass

    ###################################
    def on_stop(self):
        print("Done")
        pass


    ###################################
    def get_tick_fitness(self):
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
        pass

        return self.Calmar
