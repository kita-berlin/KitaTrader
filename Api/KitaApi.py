from __future__ import annotations
import math
import locale
from typing import TypeVar
from datetime import datetime, timedelta
from Api.KitaApiEnums import *
from Api.TradeProvider import TradeProvider
from Api.PyLogger import PyLogger
from Api.LogParams import LogParams
from Api.Account import Account
from Api.Symbol import Symbol
from Api.Position import Position
from Api.KitaApiEnums import BidAsk, TradeType, ProfitMode
from Api.QuoteProvider import QuoteProvider
from Api.Symbol import Symbol

# Define a TypeVar that can be float or int
T = TypeVar("T", float, int)


############# KitaApi ########################
class KitaApi:

    # Parameter
    # region
    # These parameters can be set by the startup module like MainConsole.py
    # If not set from there, the given default values will be used
    AllDataStartUtc: datetime
    AllDataEndUtc: datetime = datetime.max
    BacktestStartUtc: datetime
    BacktestEndUtc: datetime
    RunningMode: RunMode = RunMode.SilentBacktesting
    CachePath: str = ""
    AccountInitialBalance: float = 10000.0
    AccountLeverage: int = 500
    AccountCurrency: str = "EUR"
    # endregion

    # Members
    # region
    robot: KitaApi
    logger: PyLogger = None  # type:ignore
    # endregion

    def __init__(self):
        pass

    # Trading API
    # region
    def close_trade(
        self,
        pos: Position,
        marginAfterOpen: float,
        min_open_duration: timedelta,
        avg_open_duration_sum: timedelta,
        open_duration_count: int,
        max_open_duration: timedelta,
        is_utc: bool = True,
    ) -> bool:
        close_result = pos.symbol.trade_provider.close_position(pos)
        if close_result.is_successful:
            last_hist = self.history[-1]
            log = LogParams()
            log.symbol = pos.symbol
            log.volume_in_units = last_hist.volume_in_units
            log.trade_type = last_hist.trade_type
            log.closing_price = last_hist.closing_price
            log.entry_price = last_hist.entry_price
            log.entry_time = last_hist.entry_time
            log.closing_time = last_hist.closing_time
            log.net_profit = last_hist.net_profit
            log.comment = ""
            log.balance = self.account.balance
            log.trade_margin = last_hist.margin
            log.max_equity_drawdown = self.max_equity_drawdown_value
            # log.max_trade_equity_drawdown_value = self.max_trade_equity_drawdown_value

            self.log_closing_trade(log)
            self.log_flush

            duration = last_hist.closing_time - last_hist.entry_time  # .seconds
            if min_open_duration < duration:
                min_open_duration = duration
            avg_open_duration_sum += duration
            open_duration_count += 1
            if max_open_duration > duration:
                max_open_duration = duration

            return True
        return False

    # endregion

    # Internal API
    # region
    def request_symbol(
        self,
        symbol_name: str,
        quote_provider: QuoteProvider,
        trade_provider: TradeProvider,
        str_time_zone: str = "utc",
    ) -> tuple[str, Symbol]:
        symbol = Symbol(self, symbol_name, quote_provider, trade_provider, str_time_zone)

        quote_provider.init_symbol(self, symbol)
        trade_provider.init_symbol(self, symbol)
        self.symbol_dictionary[symbol_name] = symbol

        return "", symbol

    # endregion

    # Long/Short and other arithmetic
    # region
    def is_greater_or_equal_long(self, long_not_short: bool, val1: float, val2: float) -> bool:
        return val1 >= val2 if long_not_short else val1 <= val2

    def is_less_or_equal_long(self, long_not_short: bool, val1: float, val2: float) -> bool:
        return val1 <= val2 if long_not_short else val1 >= val2

    def is_greater_long(self, long_not_short: bool, val1: float, val2: float) -> bool:
        return val1 > val2 if long_not_short else val1 < val2

    def is_less_long(self, long_not_short: bool, val1: float, val2: float) -> bool:
        return val1 < val2 if long_not_short else val1 > val2

    def is_crossing(
        self,
        long_not_short: bool,
        a_current: float,
        a_prev: float,
        b_current: float,
        b_prev: float,
    ) -> bool:
        return self.is_greater_or_equal_long(long_not_short, a_current, b_current) and self.is_less_or_equal_long(
            long_not_short, a_prev, b_prev
        )

    def add_long(self, long_not_short: bool, val1: float, val2: float) -> float:
        return val1 + val2 if long_not_short else val1 - val2

    def sub_long(self, long_not_short: bool, val1: float, val2: float) -> float:
        return val1 - val2 if long_not_short else val1 + val2

    def diff_long(self, long_not_short: bool, val1: float, val2: float) -> float:
        return val1 - val2 if long_not_short else val2 - val1

    def i_price(self, dPrice: float, tickSize: float) -> int:
        return int(math.copysign(0.5 + abs(dPrice) / tickSize, dPrice))

    def d_price(self, price: float, tickSize: float) -> float:
        return tickSize * price

    def sharpe_sortino(self, is_sortino: bool, vals: list[float]) -> float:
        if len(vals) < 2:
            return float("nan")

        average = sum(vals) / len(vals)
        sd = math.sqrt(
            sum((val - average) ** 2 for val in vals if not is_sortino or val < average) / (len(vals) - 1)
        )
        return average / sd if sd != 0 else float("nan")

    def standard_deviation(self, is_sortino: bool, vals: list[float]) -> float:
        average = sum(vals) / len(vals)
        return math.sqrt(
            sum((val - average) ** 2 for val in vals if not is_sortino or val < average) / (len(vals) - 1)
        )

    def is_new_bar_get(self, seconds: int, time: datetime, prevTime: datetime) -> bool:
        if datetime.min == prevTime:
            return True
        return int(time.timestamp()) // seconds != int(prevTime.timestamp()) // seconds

    # endregion

    # Logging
    # region
    logging_trade_count = 0

    @property
    def is_open(self) -> bool:
        return self.log_stream_writer is not None

    def open_logfile(
        self,
        filename: str = "",
        mode: int = PyLogger.HEADER_AND_SEVERAL_LINES,
        header: str = "",
    ):
        if (
            self.RunningMode != RunMode.BruteForceOptimization
            and self.RunningMode != RunMode.GeneticOptimization
            and self.RunningMode != RunMode.WalkForwardOptimization
        ):
            self.logger = PyLogger()
            self.logger.log_open(
                self.logger.make_log_path(),
                filename,
                self.RunningMode == RunMode.RealTime,
                mode,
            )
            # if not openState:
            self.write_log_header(mode, header)

    def write_log_header(
        self,
        mode: int = PyLogger.HEADER_AND_SEVERAL_LINES,
        header: str = "",
    ):
        log_header: str = ""
        if (
            self.logger is None or not self.logger.is_open  # type: ignore
        ):  # or int(LoggerConstants.no_header) & int(self.logger.mode) != 0:
            return

        self.logger.add_text("sep =,")  # Hint for Excel

        if PyLogger.SELF_MADE == mode:
            log_header = header
        else:
            log_header += (
                "\nOpenDate,OpenTime,symbol,Lots,open_price,Swap,Swap/Lot,open_asks,open_bid,open_spread_pts"
                if 0 == (self.logger.mode & PyLogger.ONE_LINE)
                else ","
            )
            log_header += (
                ",CloseDate,ClosingTime,Mode,Volume,closing_price,commission,Comm/Lot,close_ask,close_bid,close_spread_pts"
                if 0 == (self.logger.mode & PyLogger.ONE_LINE)
                else ","
            )
            log_header += ",Number,Dur. d.h.self.s,Balance,point_value,diff_pts,diff_gross,net_profit,net_prof/Lot,account_margin,trade_margin"
            # if 0 == (self.logger.mode & one_line) log_header += (",\n")

        self.logger.add_text(log_header)
        self.logger.flush()
        self.header_split = log_header.split(",")

    def log_add_text(self, s: str):
        if self.logger is None or not self.logger.is_open:  # type: ignore
            return

        self.logger.add_text(s)

    def log_add_text_line(self, s: str):
        self.log_add_text(s + "\n")

    def log_closing_trade(self, lp: LogParams):
        if self.logger is None or not self.logger.is_open:  # type: ignore
            return

        # orgComment;123456,aaa,+-ppp     meaning:
        # openAskInPts,openSpreadInPts
        open_bid: float = 0
        open_ask: float = 0
        if lp.comment is not None:  # type: ignore
            bid_asks = lp.comment.split(";")
            if len(bid_asks) >= 2:
                bid_asks = bid_asks[1].split(",")
                if len(bid_asks) == 2:
                    i_ask = KitaApi.string_to_integer(bid_asks[0])
                    open_ask = round(lp.symbol.point_size * i_ask, lp.symbol.digits)
                    # open_bid = lp.symbol.point_size * (
                    #     i_ask - KitaApi.string_to_integer(bid_asks[1])
                    # )

        price_diff = (1 if lp.trade_type == TradeType.Buy else -1) * (lp.closing_price - lp.entry_price)
        point_diff = self.i_price(price_diff, lp.symbol.point_size)
        lot_digits = 1  # int(0.5 + math.log10(1 / lp.min_lots))

        for part in self.header_split:
            change_part = part
            if "\n" in part:
                self.logger.add_text("\n")
                change_part = part[1:]
            else:
                self.logger.add_text(",")

            if change_part == "OpenDate":
                self.logger.add_text(lp.entry_time.strftime("%Y.%m.%d"))
                continue
            elif change_part == "OpenTime":
                self.logger.add_text(lp.entry_time.strftime("%H:%M:%S"))
                continue
            elif change_part == "Symbol":
                self.logger.add_text(lp.symbol.name)
                continue
            elif change_part == "Lots":
                self.logger.add_text(KitaApi.double_to_string(lp.lots, lot_digits))
                continue
            elif change_part == "OpenPrice":
                self.logger.add_text(KitaApi.double_to_string(lp.entry_price, lp.symbol.digits))
                continue
            elif change_part == "Swap":
                self.logger.add_text(KitaApi.double_to_string(lp.swap, 2))
                continue
            elif change_part == "Swap/Lot":
                self.logger.add_text(KitaApi.double_to_string(lp.swap / lp.lots, 2))
                continue
            elif change_part == "OpenAsks":
                self.logger.add_text(
                    KitaApi.double_to_string(open_ask, lp.symbol.digits) if lp.trade_type == TradeType.Buy else ""
                )
                continue
            elif change_part == "OpenBid":
                self.logger.add_text(
                    KitaApi.double_to_string(open_bid, lp.symbol.digits) if lp.trade_type == TradeType.Sell else ""
                )
                continue
            elif change_part == "OpenSpreadPoints":
                self.logger.add_text(
                    KitaApi.double_to_string(self.i_price((open_ask - open_bid), lp.symbol.point_size), 0)
                )
                continue
            elif change_part == "CloseDate":
                self.logger.add_text(lp.closing_time.strftime("%Y.%m.%d"))
                continue
            elif change_part == "ClosingTime":
                self.logger.add_text(lp.closing_time.strftime("%H:%M:%S"))
                continue
            elif change_part == "Mode":
                self.logger.add_text("Short" if lp.trade_type == TradeType.Sell else "Long")
                continue
            elif change_part == "PointValue":
                self.logger.add_text(KitaApi.double_to_string(self.get_money_from_1point_and_1lot(lp.symbol), 5))
                continue
            elif change_part == "ClosingPrice":
                self.logger.add_text(KitaApi.double_to_string(lp.closing_price, lp.symbol.digits))
                continue
            elif change_part == "Commission":
                self.logger.add_text(KitaApi.double_to_string(lp.commissions, 2))
                continue
            elif change_part == "Comm/Lot":
                self.logger.add_text(KitaApi.double_to_string(lp.commissions / lp.lots, 2))
                continue
            elif change_part == "CloseAsk":
                self.logger.add_text(
                    "{:.{}f}".format(self.get_bid_ask_price(lp.symbol, BidAsk.Ask), lp.symbol.digits)
                    if lp.trade_type == TradeType.Sell
                    else ""
                )
                continue
            elif change_part == "CloseBid":
                self.logger.add_text(
                    KitaApi.double_to_string(self.get_bid_ask_price(lp.symbol, BidAsk.Bid), lp.symbol.digits)
                    if lp.trade_type == TradeType.Buy
                    else ""
                )
                continue
            elif change_part == "CloseSpreadPoints":
                self.logger.add_text(
                    KitaApi.double_to_string(
                        self.i_price(
                            self.get_bid_ask_price(lp.symbol, BidAsk.Ask)
                            - self.get_bid_ask_price(lp.symbol, BidAsk.Bid),
                            lp.symbol.point_size,
                        ),
                        0,
                    )
                )
                continue
            elif change_part == "Balance":
                self.logger.add_text(KitaApi.double_to_string(lp.balance, 2))
                continue
            elif change_part == "Dur. d.h.self.s":
                self.logger.add_text(str(lp.entry_time - lp.closing_time).rjust(11, " "))
                continue
            elif change_part == "Number":
                self.logging_trade_count += 1
                self.logger.add_text(KitaApi.integer_to_string(self.logging_trade_count))
                continue
            elif change_part == "Volume":
                self.logger.add_text(KitaApi.double_to_string(lp.volume_in_units, 1))
                continue
            elif change_part == "DiffPoints":
                self.logger.add_text(KitaApi.double_to_string(point_diff, 0))
                continue
            elif change_part == "DiffGross":
                self.logger.add_text(
                    KitaApi.double_to_string(
                        self.get_money_from_points_and_lot(lp.symbol, point_diff, lp.lots),
                        2,
                    )
                )
                continue
            elif change_part == "net_profit":
                self.logger.add_text(KitaApi.double_to_string(lp.net_profit, 2))
                continue
            elif change_part == "NetProf/Lot":
                self.logger.add_text(KitaApi.double_to_string(lp.net_profit / lp.lots, 2))
                continue
            elif change_part == "AccountMargin":
                self.logger.add_text(KitaApi.double_to_string(lp.account_margin, 2))
                continue
            elif change_part == "TradeMargin":
                self.logger.add_text(KitaApi.double_to_string(lp.trade_margin, 2))
                continue
            elif change_part == "MaxEquityDrawdown":
                self.logger.add_text(KitaApi.double_to_string(lp.max_equity_drawdown, 2))
                continue
            elif change_part == "MaxTradeEquityDrawdownValue":
                self.logger.add_text(KitaApi.double_to_string(lp.max_trade_equity_drawdown_value, 2))
                continue
            else:
                pass

        self.logger.flush()

    def log_flush(self):
        if self.logger is None or not self.logger.is_open:  # type: ignore
            return
        self.logger.flush()

    def log_close(self, header_line: str = ""):
        if self.logger is None or not self.logger.is_open:  # type: ignore
            return

        self.logger.close(header_line)
        self.log_stream_writer = None

    # endregion

    # Price and lot/volume calculation
    # region
    @staticmethod
    def get_bid_ask_price(symbol: Symbol, bidAsk: BidAsk):
        return symbol.bid if bidAsk == BidAsk.Bid else symbol.ask

    @staticmethod
    def get_lots_from_profitmode(
        symbol: Symbol,
        profitMode: ProfitMode,
        value: float,
        tpPts: int,
        riskPoints: int,
        desired_money: list[float],
        lot_size: list[float],
    ):
        desired_money[0] = 0
        lot_size[0] = 0

        if math.isnan(symbol.point_value):
            return "Invalid point_value"
        """
        if ProfitMode == ProfitMode.lots:
            desi_mon = self.get_money_from_points_and_lot(symbol: Symbol, tpPts, lot_siz =value)
        elif ProfitMode == ProfitMode.lots_pro10k:
            lot_siz = (self.account.balance - self.account.margin) / 10000 * value
            desi_mon = self.get_money_from_points_and_lot(symbol: Symbol, tpPts, lot_size)
        elif ProfitMode == ProfitMode.profit_percent:
            desi_mon = (self.account.balance - self.account.margin) * value / 100
            lot_siz = self.get_lots_from_money_and_points(symbol: Symbol, desired_money, tpPts, self.commission_per_lot(symbol: Symbol))
        elif ProfitMode == ProfitMode.profit_ammount:
            lot_siz = self.get_lots_from_money_and_points(symbol: Symbol, desi_mon =value, tp_pts =tpPts, x_pro_lot =self.commission_per_lot(symbol: Symbol))
        elif profitMode in [ProfitMode.risk_constant, ProfitMode.risk_reinvest]:
            balance = self.account.balance if ProfitMode == ProfitMode.risk_reinvest else self.initial_account_balance
            money_to_risk = (balance - self.account.margin) * value / 100
            lot_siz = self.get_lots_from_money_and_points(symbol: Symbol, moneyToRisk, riskPoints, self.commission_per_lot(symbol: Symbol))
            desi_mon = self.get_money_from_points_and_lot(symbol: Symbol, tpPts, lot_size)
        elif profitMode in [ProfitMode.constant_invest, ProfitMode.Reinvest]:
            invest_money = (self.initial_account_balance if ProfitMode == ProfitMode.constant_invest else self.account.balance) * value / 100
            units = investMoney * symbol.point_size / symbol.point_value / symbol.bid
            lot_siz = symbol.volume_in_units_to_quantity(units)
            desi_mon = self.get_money_from_points_and_lot(symbol: Symbol, tpPts, lot_size)
        """
        return ""

    @staticmethod
    def get_money_from_points_and_lot(symbol: Symbol, points: int, lot: float) -> float:
        return symbol.point_value * symbol.lot_size * points * lot

    @staticmethod
    def get_money_from_points_and_volume(symbol: Symbol, points: int, volume: float) -> float:
        return symbol.point_value * points * volume / symbol.lot_size

    @staticmethod
    def get_money_from_1point_and_1lot(symbol: Symbol, reverse: bool = False):
        ret_val = KitaApi.get_money_from_points_and_lot(symbol, 1, 1)
        if reverse:
            ret_val *= symbol.bid
        return ret_val

    @staticmethod
    def get_points_from_money_and_lot(symbol: Symbol, money: float, lot: float):
        return money / (lot * symbol.point_value * symbol.lot_size)

    @staticmethod
    def get_points_from_money_and_volume(symbol: Symbol, money: float, volume: float):
        return money / (volume * symbol.point_value)

    @staticmethod
    def get_lots_from_money_and_points(symbol: Symbol, money: float, points: int, xProLot: float):
        ret_val = abs(money / (points * symbol.point_value * symbol.lot_size + xProLot))
        ret_val = max(ret_val, symbol.min_volume)
        ret_val = min(ret_val, symbol.max_volume)
        return ret_val
        # endregion

    # Methods
    # region

    def init(self):
        self.robot = self
        self.account: Account = Account(self)
        self.account.balance = self.AccountInitialBalance
        self.account.leverage = self.AccountLeverage
        self.account.currency = self.AccountCurrency

        self.is_train: bool = False
        self.initial_account_balance: float = self.AccountInitialBalance
        self.symbol_dictionary: dict[str, Symbol] = {}  # type: ignore
        self.positions: list[Position] = []
        self.history: list[Position] = []
        self.max_margin: float = 0
        self.same_time_open: int = 0
        self.max_balance: float = 0
        self.max_balance_drawdown_value: float = 0
        self.max_equity: float = 0
        self.max_equity_drawdown_value: float = 0
        self.min_open_duration: timedelta = timedelta.max
        self.avg_open_duration_sum: timedelta = timedelta.min
        self.open_duration_count: int = 0
        self.max_open_duration: timedelta = timedelta.min
        self.same_time_open_date_time = datetime.min
        self.same_time_open_count = 0
        self.max_balance_drawdown_time = datetime.min
        self.max_balance_drawdown_count = 0
        self.max_equity_drawdown_time = datetime.min
        self.max_equity_drawdown_count = 0
        self.current_volume = 0
        self.initial_volume = 0

        # call robot's OnInit
        self.robot.on_init()  # type: ignore

        # load bars and data rate
        for symbol in self.symbol_dictionary.values():
            symbol.load_datarate_and_bars()

    def start(self):
        for symbol in self.symbol_dictionary.values():
            self.robot.on_start(symbol)  # type: ignore

    def tick(self):
        # Update quote, bars, indicators, account, bot
        # 1st tick must update all bars and Indicators which have been inized in on_init()
        for symbol in self.symbol_dictionary.values():

            # Update quote, bars, indicators which are bound to this symbol
            error = symbol.symbol_on_tick()
            if "" != error or symbol.time > symbol.end_tz_dt:
                return True  # end reached

            # Update Account
            if len(self.positions) >= 1:
                symbol.trade_provider.update_account()

            # call the robot
            self.robot.on_tick(symbol)  # type: ignore

            # do max/min calcs
            # region
            self.max_margin = max(self.max_margin, self.account.margin)
            if  len(self.positions) > self.same_time_open:
                self.same_time_open = len(self.positions)
                self.same_time_open_date_time = symbol.time
                self.same_time_open_count = len(self.history)

            self.max_balance = max(self.max_balance, self.account.balance)
            if  self.max_balance - self.account.balance > self.max_balance_drawdown_value:
                self.max_balance_drawdown_value = self.max_balance - self.account.balance
                self.max_balance_drawdown_time = symbol.time
                self.max_balance_drawdown_count = len(self.history)

            self.max_equity = max(self.max_equity, self.account.equity)
            if  self.max_equity - self.account.equity > self.max_equity_drawdown_value:
                self.max_equity_drawdown_value = self.max_equity - self.account.equity
                self.max_equity_drawdown_time = symbol.time
                self.max_equity_drawdown_count = len(self.history)
            # endregion

            symbol.prev_time = symbol.time

        return False

    def stop(self):
        # call bot
        self.robot.on_stop()  # type: ignore

        # calc performance numbers
        min_duration = timedelta.max
        max_duration = timedelta.min
        duration_count = 0
        duration_count += self.open_duration_count
        min_duration = min(self.min_open_duration, min_duration)
        max_duration = max(self.max_open_duration, max_duration)

        winning_trades = len([x for x in self.history if x.net_profit >= 0])
        losing_trades = len([x for x in self.history if x.net_profit < 0])
        net_profit = sum(x.net_profit for x in self.history)
        trading_days = 0
        for symbol in self.symbol_dictionary.values():
            trading_days = (  # 365 - 2*52 = 261 - 9 holidays = 252
                (symbol.time - symbol.start_tz_dt).days / 365.0 * 252.0
            )
            break

        if 0 == trading_days:
            annual_profit = 0
        else:
            annual_profit = net_profit / (trading_days / 252.0)
        total_trades = winning_trades + losing_trades
        annual_profit_percent = 0 if total_trades == 0 else 100.0 * annual_profit / self.initial_account_balance
        loss = sum(x.net_profit for x in self.history if x.net_profit < 0)
        profit = sum(x.net_profit for x in self.history if x.net_profit >= 0)
        profit_factor = 0 if losing_trades == 0 else abs(profit / loss)
        max_current_equity_dd_percent = 100 * self.max_equity_drawdown_value / self.max_equity
        max_start_equity_dd_percent = 100 * self.max_equity_drawdown_value / self.initial_account_balance
        calmar = 0 if self.max_equity_drawdown_value == 0 else annual_profit / self.max_equity_drawdown_value
        winning_ratio_percent = 0 if total_trades == 0 else 100.0 * winning_trades / total_trades

        if 0 == trading_days:
            trades_per_month = 0
        else:
            trades_per_month = total_trades / (trading_days / 252.0) / 12.0

        sharpe_ratio = self.sharpe_sortino(False, [trade.net_profit for trade in self.history])
        sortino_ratio = self.sharpe_sortino(True, [trade.net_profit for trade in self.history])

        # some proofs
        # percent_sharpe_ratio = self.sharpe_sortino(
        #     False,
        #     [trade.net_profit / self.initial_account_balance for trade in self.history],
        # )

        # vals = [trade.net_profit for trade in self.history]
        # average = sum(vals) / len(vals)
        # sd = self.standard_deviation(False, vals)
        # # my_sharpe = average / sd
        # # Baron
        # average_daily_return = annual_profit / 252.0
        # sharpe_ratio = average_daily_return / sd * sqrt(252.0)

        log_text = "\n\n" + (
            "Net Profit:,"
            + KitaApi.double_to_string(profit + loss, 2)
            + ", Long:,"
            + KitaApi.double_to_string(
                sum(x.net_profit for x in self.history if x.trade_type == TradeType.Buy),
                2,
            )
            + ", Short:,"
            + KitaApi.double_to_string(
                sum(x.net_profit for x in self.history if x.trade_type == TradeType.Sell),
                2,
            )
            + "\n"
        )

        log_text += (
            "All Trades:,"
            + str(total_trades)
            + ", Winners:,"
            + str(winning_trades)
            + ", Losers:,"
            + str(losing_trades)
            + "\n"
        )

        # log_text += ("max_margin: " + self.account.asset + " " + KitaApi.double_to_string(mMaxMargin, 2) + "\n")
        # log_text += ("max_same_time_open: " + str(mSameTimeOpen + "\n")
        # + ", @ " + mSameTimeOpenDateTime.strftime("%d.%m.%Y %H:%M:%S")
        # + ", Count# " + str(mSameTimeOpenCount))
        log_text += (
            "Max Balance Drawdown Value: "
            + self.account.currency
            + " "
            + KitaApi.double_to_string(self.max_balance_drawdown_value, 2)
            + "; @ "
            + self.max_balance_drawdown_time.strftime("%d.%m.%Y %H:%M:%S")
            + "; Count# "
            + str(self.max_balance_drawdown_count)
            + "\n"
        )

        log_text += (
            "Max Balance Drawdown%: "
            + (
                "NaN"
                if self.max_balance == 0
                else KitaApi.double_to_string(100 * self.max_balance_drawdown_value / self.max_balance, 2)
            )
            + "\n"
        )

        log_text += (
            "Max Equity Drawdown Value: "
            + self.account.currency
            + " "
            + KitaApi.double_to_string(self.max_equity_drawdown_value, 2)
            + "; @ "
            + self.max_equity_drawdown_time.strftime("%d.%m.%Y %H:%M:%S")
            + "; Count# "
            + str(self.max_equity_drawdown_count)
            + "\n"
        )

        log_text += (
            "Max Current Equity Drawdown %: " + KitaApi.double_to_string(max_current_equity_dd_percent, 2) + "\n"
        )

        log_text += (
            "Max start Equity Drawdown %: " + KitaApi.double_to_string(max_start_equity_dd_percent, 2) + "\n"
        )

        log_text += (
            "Profit Factor: " + ("-" if losing_trades == 0 else KitaApi.double_to_string(profit_factor, 2)) + "\n"
        )

        log_text += "Sharpe Ratio: " + KitaApi.double_to_string(sharpe_ratio, 2) + "\n"
        log_text += "Sortino Ratio: " + KitaApi.double_to_string(sortino_ratio, 2) + "\n"
        log_text += "Calmar Ratio: " + KitaApi.double_to_string(calmar, 2) + "\n"
        log_text += "Winning Ratio: " + KitaApi.double_to_string(winning_ratio_percent, 2) + "\n"
        log_text += "Trades Per Month: " + KitaApi.double_to_string(trades_per_month, 2) + "\n"
        log_text += "Average Annual Profit Percent: " + KitaApi.double_to_string(annual_profit_percent, 2) + "\n"

        # if avg_open_duration_sum != 0:
        #     log_text += (
        #         "Min / Avg / Max Tradeopen Duration (Day.Hour.Min.sec): "
        #         + str(min_duration)
        #         + " / "
        #         + str(avg_open_duration_sum / avg_open_duration_sum)
        #         + " / "
        #         + str(self.max_duration)
        #     ) + "\n"

        # histo_rest_sum = 0.0
        # if investCountHisto is not None:
        #     for i in range(len(investCountHisto) - 1, 0, -1):
        #         if investCountHisto[i] != 0:
        #             log_text += ("Invest " + str(i) + ": " + str(investCountHisto[i]))
        #             if i > 1:
        #                 histoRestSum += investCountHisto[i]
        #     if histoRestSum != 0:
        #         log_text += ("histo_rest_quotient: " + KitaApi.double_to_string(m_histo_rest_quotient = investCountHisto[1] / histoRestSum,
        print(log_text.replace(":,", ": "))
        self.log_add_text_line(log_text)
        self.log_close()

    def calculate_reward(self) -> float:
        return self.robot.get_tick_fitness()  # type:ignore

    @staticmethod
    def double_to_string(value: float, digits: int) -> str:
        if value == float("inf") or value != value:
            return "NaN"
        format_str = "{:." + str(digits) + "f}"
        return format_str.format(value)

    @staticmethod
    def integer_to_string(n: int) -> str:
        return str(n)

    @staticmethod
    def string_to_double(s: str) -> float:
        try:
            return locale.atof(s)
        except ValueError:
            return 0

    @staticmethod
    def string_to_integer(s: str) -> int:
        try:
            return int(s)
        except ValueError:
            return 0

    # endregion


# end of file