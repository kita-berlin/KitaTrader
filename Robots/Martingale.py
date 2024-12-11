from math import sqrt
from KitaApiEnums import *
from KitaApi import KitaApi
from Api.CoFu import *
from Constants import *
from KitaApi import Symbol, PyLogger
from talib import MA_Type  # type: ignore

from TradePaper import TradePaper
from QuoteMe import QuoteMe  # type: ignore
from QuoteDukascopy import Dukascopy  # type: ignore
from QuoteTradeMt5 import BrokerMt5  # type: ignore
from QuoteCsv import QuoteCsv  # type: ignore


class Martingale(KitaApi):

    # History
    # region
    version: str = "Martingale V1.0"
    # V1.0     14.02.23    HMz created
    # endregion

    # Parameter
    # region
    # These parameters can be set by the startup module like MainConsole.py
    # If not set from there, the given default values will be used
    Rebuy1stPercent = 1.5
    RebuyPercent = 0.2
    TakeProfitPercent = 0.2
    Volume = 2000
    Direction = TradeDirection.Mode1
    # endregion

    # Members
    # region
    def __init__(self):
        super().__init__()  # Importatnt, do not delete

    sqrt252: float = sqrt(252)
    # endregion

    ###################################
    def on_init(self) -> None:

        # Members; We do declaration here so members will be reinized by 2nd++ on_init()
        # region
        self.is_long = True
        self.current_volume = self.initial_volume = self.Volume
        self.max_invest_count: list[int] = [0] * 1
        self.cluster_count: int = 0
        self.avg_price: float = 0
        self.invest_count: int = 0
        self.current_volume: float = 0
        self.cluster_profit: float = 0
        self.daily_revenue: list[float] = []
        self.prev_revenue: float = 0
        self.sharpe_ratio: float = 0
        self.sortino_ratio: float = 0
        self.calmar: float = 0
        self.is_train: bool = False
        # endregion

        # Logging
        # region
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

        self.log_mode = PyLogger.SELF_MADE
        self.open_logfile(self.version.split(" ")[0] + ".csv", self.log_mode, header)
        self.log_flush()
        # endregion

        # Possible quote_providers
        # datarate is in seconds, 0 means fastetst possible (i.e. Ticks)
        quote_provider = Dukascopy("", datarate=0)
        # quote_provider = QuoteMe("G:\\Meine Ablage\\TickBars", datarate=0),
        # quote_provider = BrokerMt5("62060378, pepperstone_uk-Demo, tFue0y*akr", datarate=0)
        # quote_provider = QuoteCsv("G:\\Meine Ablage", datarate=0)

        # Demo to show all available symbols
        i = 0
        for symbol_name in quote_provider.symbols:
            i = i + 1
            print(str(i) + ": " + symbol_name)

        # error, symbol =
        self.load_symbol(
            "NZDCAD",
            quote_provider,
            # Paper trading
            TradePaper(""),
            # If :Normalized is added to America/New_York, 7 hours are added
            # This gives New York 17:00 = midnight so that forex trading runs from Moday 00:00 - Friday 23:59:59
            # (we call this "New York normalized time")
            "America/New_York:Normalized",
        )

        # Example how to use bars
        # if "" == error:
        #     error, m1_bars = symbol.load_bars(Constants.SEC_PER_MINUTE)
        #     m1_bars.count

        """ example how to use indicators
        self.time_period = 14
        self.indi_bars = self.market_data.load_bars(SEC_PER_HOUR, self.symbol.name)
        
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
                "Time, Direction, Profit, max_equity_draw_down, cluster_count, invest_count, calmar, Rebuy1st%, Rebuy%, take_profit%"
            )

    ###################################
    def on_tick(self, symbol: Symbol):
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

        current_open = symbol.ask if self.is_long else symbol.bid
        current_close = symbol.bid if self.is_long else symbol.ask
        target_cash = current_repurchase_price = 0

        # Check spread
        is_spread = True
        if (
            symbol.spread < 0
            or symbol.spread > 2 * symbol.avg_spread * symbol.point_size
        ):
            is_spread = False
        is_trading_allowed = is_spread

        # Init some vars if 0 positions open
        if 0 == self.invest_count:
            self.cluster_profit = 0
            self.current_volume = self.initial_volume
        pass

        # Calc some vars if some positions are open
        if self.invest_count >= 1:
            last_position = self.positions[-1]
            self.cluster_profit = self.current_volume = 0
            cluster_price_by_volume_sum = 0

            for pos in self.positions:
                self.cluster_profit += pos.net_profit
                cluster_price_by_volume_sum += pos.entry_price * pos.volume_in_units
                self.current_volume += pos.volume_in_units

            self.avg_price = cluster_price_by_volume_sum / self.current_volume

            current_repurchase_price = self.sub_long(
                self.is_long,
                last_position.entry_price,
                last_position.entry_price
                * (self.Rebuy1stPercent if self.invest_count < 2 else self.RebuyPercent)
                / 100,
            )

            tp_value = current_close * self.TakeProfitPercent / 100
            # tp_price = self.add_long(self.is_long, self.avg_price, tp_value)
            tp_points = self.i_price(tp_value, symbol.point_size)

            target_cash = self.get_money_from_points_and_volume(
                symbol, tp_points, self.current_volume
            )
        pass

        # Take Profit ?
        is_just_closed = False
        if is_trading_allowed:
            if self.invest_count > 0:
                # check profit instead of price because of swaps etc.
                if self.cluster_profit > target_cash:
                    self.close_all_open_positions()  # close all open trades

                    # "Time; Profit; max_equity_draw_down; cluster_count; invest_count; calmar; Rebuy1st%; Rebuy%; take_profit%"
                    if not self.is_train:
                        print(
                            symbol.time.strftime("%d-%m-%Y %H:%M:%S; ")
                            + ("Long" if self.is_long else "Short")
                            # + "; {:.2f}".format(
                            #     self.account.balance - self.initial_account_balance
                            # )
                            + "; {:.2f}".format(self.max_equity_drawdown_value[0])
                            + "; {}".format(self.cluster_count)
                            + "; {}".format(self.invest_count)
                            + "; {:.2f}".format(self.calmar)
                        )

                    if self.Direction == TradeDirection.Mode1:
                        self.is_long = not self.is_long  # flip direction
                    is_just_closed = True
        pass

        # Open ?
        if is_trading_allowed and not is_just_closed:
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
                # wie sollen die Parameter Rebuy1stPercent, RebuyPercent
                # und TakeProfitPercent aussehen?
                # Das volume_to_add beeinflusst den Mischpreis (self.avg_price)
                # und zieht ihn näher zum aktuellen Preis hin
                pos = self.execute_market_order(
                    TradeType.Buy if self.is_long else TradeType.Sell,
                    symbol.name,
                    symbol.normalize_volume_in_units(volume_to_add),
                    self.get_label(symbol),
                )

                self.invest_count += 1
                self.max(self.max_invest_count, self.invest_count)
                self.margin_after_open = self.account.margin

                if not self.is_train:
                    print(
                        symbol.time.strftime("%d-%m-%Y %H:%M:%S; ")
                        + ("Long" if self.is_long else "Short")
                        + "; {:.2f}".format(
                            self.account.balance - self.initial_account_balance
                        )
                        # + "; {:.2f}".format(self.max_equity_drawdown_value[0])
                        # + "; {}".format(self.cluster_count)
                        # + "; {}".format(self.invest_count)
                        # + "; {:.2f}".format(self.calmar)
                        # + "; {:.2f}".format(self.Rebuy1stPercent)
                        # + "; {:.2f}".format(self.RebuyPercent)
                        # + "; {:.2f}".format(self.TakeProfitPercent)
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
    def get_label(self, symbol: Symbol):
        return (
            f"{self.version};"
            f"{self.cluster_count}_{self.invest_count};"
            f"{int(0.5 + (symbol.ask if self.is_long else symbol.bid) / symbol.point_size)};"
            f"{symbol.time};"
        )

    ###################################
    def close_all_open_positions(self):
        # is_cluster = len(self.positions) >= 2
        # if isCluster:
        #     self.log_add_text("\n")

        for pos in self.positions:
            self.close_trade(
                pos,
                self.margin_after_open,
                self.min_open_duration,
                self.avg_open_duration_sum,
                self.open_duration_count,
                self.max_open_duration,
            )

        # if isCluster:
        self.log_add_text("\n")

        self.cluster_count += 1
        self.positions = []
        self.invest_count = 0

    ###################################
    def get_tick_fitness(self) -> float:
        # ret_val = 0.0
        self.history  # list of closed positions
        self.positions  # list of current open positions; Count matches self.invest_count
        self.initial_account_balance  # start balance
        self.account.balance  # start balance plus profit sum of all CLOSED positions (sum of REALIZED profit)
        self.account.equity  # self.account.balance plus profit sum of all OPEN positions (sum of UNREALIZED profit)
        self.cluster_count  # number of current cluster
        self.invest_count  # number of open trades within current cluster
        self.account.margin  # sum of all open Position margins; equal to sum(x.margin for x in self.positions)
        self.max_equity_drawdown_value[
            0
        ]  # holds biggest difference of self.account.balance and self.account.equity

        # composed values
        history_profit = self.account.balance - self.initial_account_balance
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
