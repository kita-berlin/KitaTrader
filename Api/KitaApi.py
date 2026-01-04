from __future__ import annotations
import os
import re
import math
import time
from typing import TypeVar
from datetime import datetime, timedelta, date
from typing import Optional
import pytz
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
from Api.CoFu import CoFu
from Indicators.Indicators import Indicators
from Api.MarketData import MarketData

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
    BacktestStart: datetime  
    BacktestEnd: datetime    
    _BacktestStartUtc: datetime = datetime.min  # Internal: UTC version of BacktestStart
    _BacktestEndUtc: datetime = datetime.max    # Internal: UTC version of BacktestEnd
    
    @property
    def BacktestStartUtc(self) -> datetime:
        """Public property: UTC version of BacktestStart"""
        return self._BacktestStartUtc
    
    @property
    def BacktestEndUtc(self) -> datetime:
        """Public property: UTC version of BacktestEnd"""
        return self._BacktestEndUtc
    RunningMode: RunMode = RunMode.SilentBacktesting
    DataPath: str = ""
    AccountInitialBalance: float = 10000.0
    AccountLeverage: int = 500
    AccountCurrency: str = "EUR"
    # endregion

    # Members
    # region
    robot: KitaApi
    logger: PyLogger = None  # type:ignore
    _stop_requested: bool = False
    quote_provider: QuoteProvider = None  # type:ignore  # Can be set from MainConsole
    trade_provider: TradeProvider = None  # type:ignore  # Can be set from MainConsole
    Indicators: Indicators = None  # type:ignore  # Central API for creating indicators
    MarketData: MarketData = None  
    _debug_log_file = None  # Debug log file handle
    _last_ontick_date: Optional[str] = None  # Track last date printed for OnTick message
    # endregion

    def __init__(self):
        
        self.Indicators = Indicators(api=self)
        
        self.MarketData = MarketData(api=self)
        # Initialize debug log file
        self._init_debug_log()
        self._prepared = False # Flag to ensure we only prepare once after indicators are set
    
    def _init_debug_log(self):
        """Initialize debug log file"""
        log_dir = r"C:\Users\HMz\Documents\cAlgo\Logfiles"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        # Use robot class name for debug log filename (get from robot attribute if available)
        if hasattr(self, 'robot') and hasattr(self.robot, '__class__'):
            robot_name = self.robot.__class__.__name__
        else:
            robot_name = self.__class__.__name__
        debug_log_path = os.path.join(log_dir, f"{robot_name}_Debug.log")
        self._debug_log_file = open(debug_log_path, "w", encoding="utf-8")
    
    def _debug_log(self, message: str):
        """Write debug message to debug log file"""
        if self._debug_log_file:
            self._debug_log_file.write(f"{message}\n")
            self._debug_log_file.flush()

    # API for robots
    # region
    # close a position with logging; logger must be set up in the robot on_init or on_start
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

    # request a symbol to work with in the robot
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

    # Function to resolve environment variables in a template string
    def resolve_env_variables(self, template: str) -> str:
        # Find all environment variable placeholders (e.g., $(Env1))
        matches = re.findall(r"\$\((\w+)\)", template)

        # Replace each placeholder with its value from the environment
        resolved_path = template
        for match in matches:
            env_value = os.getenv(match, f"<{match}>")  # Default to placeholder if not found
            resolved_path = resolved_path.replace(f"$({match})", env_value)

        return resolved_path

    def stop(self):
        self._stop_requested = True

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
                    i_ask = int(bid_asks[0])
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
                self.logger.add_text(CoFu.double_to_string(lp.lots, lot_digits))
                continue
            elif change_part == "OpenPrice":
                self.logger.add_text(CoFu.double_to_string(lp.entry_price, lp.symbol.digits))
                continue
            elif change_part == "Swap":
                self.logger.add_text(CoFu.double_to_string(lp.swap, 2))
                continue
            elif change_part == "Swap/Lot":
                self.logger.add_text(CoFu.double_to_string(lp.swap / lp.lots, 2))
                continue
            elif change_part == "OpenAsks":
                self.logger.add_text(
                    CoFu.double_to_string(open_ask, lp.symbol.digits) if lp.trade_type == TradeType.Buy else ""
                )
                continue
            elif change_part == "OpenBid":
                self.logger.add_text(
                    CoFu.double_to_string(open_bid, lp.symbol.digits) if lp.trade_type == TradeType.Sell else ""
                )
                continue
            elif change_part == "OpenSpreadPoints":
                self.logger.add_text(
                    CoFu.double_to_string(self.i_price((open_ask - open_bid), lp.symbol.point_size), 0)
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
                self.logger.add_text(CoFu.double_to_string(self.get_money_from_1point_and_1lot(lp.symbol), 5))
                continue
            elif change_part == "ClosingPrice":
                self.logger.add_text(CoFu.double_to_string(lp.closing_price, lp.symbol.digits))
                continue
            elif change_part == "Commission":
                self.logger.add_text(CoFu.double_to_string(lp.commissions, 2))
                continue
            elif change_part == "Comm/Lot":
                self.logger.add_text(CoFu.double_to_string(lp.commissions / lp.lots, 2))
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
                    CoFu.double_to_string(self.get_bid_ask_price(lp.symbol, BidAsk.Bid), lp.symbol.digits)
                    if lp.trade_type == TradeType.Buy
                    else ""
                )
                continue
            elif change_part == "CloseSpreadPoints":
                self.logger.add_text(
                    CoFu.double_to_string(
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
                self.logger.add_text(CoFu.double_to_string(lp.balance, 2))
                continue
            elif change_part == "Dur. d.h.self.s":
                self.logger.add_text(str(lp.entry_time - lp.closing_time).rjust(11, " "))
                continue
            elif change_part == "Number":
                self.logging_trade_count += 1
                self.logger.add_text(str(self.logging_trade_count))
                continue
            elif change_part == "Volume":
                self.logger.add_text(CoFu.double_to_string(lp.volume_in_units, 1))
                continue
            elif change_part == "DiffPoints":
                self.logger.add_text(CoFu.double_to_string(point_diff, 0))
                continue
            elif change_part == "DiffGross":
                self.logger.add_text(
                    CoFu.double_to_string(
                        self.get_money_from_points_and_lot(lp.symbol, point_diff, lp.lots),
                        2,
                    )
                )
                continue
            elif change_part == "net_profit":
                self.logger.add_text(CoFu.double_to_string(lp.net_profit, 2))
                continue
            elif change_part == "NetProf/Lot":
                self.logger.add_text(CoFu.double_to_string(lp.net_profit / lp.lots, 2))
                continue
            elif change_part == "AccountMargin":
                self.logger.add_text(CoFu.double_to_string(lp.account_margin, 2))
                continue
            elif change_part == "TradeMargin":
                self.logger.add_text(CoFu.double_to_string(lp.trade_margin, 2))
                continue
            elif change_part == "MaxEquityDrawdown":
                self.logger.add_text(CoFu.double_to_string(lp.max_equity_drawdown, 2))
                continue
            elif change_part == "MaxTradeEquityDrawdownValue":
                self.logger.add_text(CoFu.double_to_string(lp.max_trade_equity_drawdown_value, 2))
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

    def _calculate_indicator_warmup_period(self) -> timedelta:
        """
        Calculate the warm-up period needed for all indicators across all symbols.
        New Architecture: max(periods + 1) * timeframe_seconds.
        """
        from Api.Constants import Constants
        
        max_warmup_seconds = 0
        max_warmup_info = None
        
        # METHOD 1: Use Indicators API tracked indicators
        if self.Indicators is not None and len(self.Indicators._created_indicators) > 0:
            for info in self.Indicators._created_indicators:
                # Use periods + 1 bar as buffer
                warmup_seconds = (info.periods + 1) * info.timeframe_seconds
                if warmup_seconds > max_warmup_seconds:
                    max_warmup_seconds = warmup_seconds
                    max_warmup_info = f"{info.indicator_name}(periods={info.periods}) on {info.timeframe_seconds}s bars"
        
        # METHOD 2: Check Bars look_back as fallback
        for symbol in self.symbol_dictionary.values():
            for bars in symbol.bars_dictonary.values():
                if bars.look_back > 0:
                    warmup_seconds_from_lookback = bars.look_back * bars.timeframe_seconds
                    if warmup_seconds_from_lookback > max_warmup_seconds:
                        max_warmup_seconds = warmup_seconds_from_lookback
                        max_warmup_info = f"Bars look_back={bars.look_back} on {bars.timeframe_seconds}s timeframe"
        
        warmup_timedelta = timedelta(seconds=max_warmup_seconds)
        
        if max_warmup_info:
            warmup_days = warmup_timedelta.total_seconds() / Constants.SEC_PER_DAY
            self._debug_log(f"Indicator warm-up calculation: Longest requirement is {max_warmup_info} = {warmup_days:.2f} days total")
        else:
            self._debug_log("Indicator warm-up calculation: No indicators or look_back found, using 0 warm-up")
        
        return warmup_timedelta

    def _convert_date_to_utc_midnight(self, date_datetime: datetime) -> datetime:
        """
        Convert a date to UTC 00:00 (midnight UTC).
        This UTC midnight where dates are interpreted as UTC 00:00.
        
        Args:
            date_datetime: datetime with date only (time will be set to 00:00 UTC)
        
        Returns:
            datetime at UTC 00:00 (naive, for compatibility)
        """
        # Set time to 00:00 UTC (midnight)
        utc_datetime = date_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
        return utc_datetime  # Return naive UTC datetime for compatibility

    def do_init(self):
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

        # set working data path
        self.robot.DataPath = self.resolve_env_variables(self.robot.DataPath)

        # Convert BacktestStart/BacktestEnd to UTC
        # If BacktestStart/BacktestEnd have time components (hours:minutes:seconds), preserve them
        
        if hasattr(self, 'BacktestStart') and self.BacktestStart != datetime.min:
            # Check if time components are set (not midnight)
            if self.BacktestStart.hour == 0 and self.BacktestStart.minute == 0 and self.BacktestStart.second == 0 and self.BacktestStart.microsecond == 0:
                # Date only - convert to UTC midnight
                self._BacktestStartUtc = self._convert_date_to_utc_midnight(self.BacktestStart)
                self._debug_log(f"BacktestStart: {self.BacktestStart} -> UTC 00:00: {self._BacktestStartUtc}")
            else:
                # Has time components - use as-is (assumed to be UTC)
                self._BacktestStartUtc = self.BacktestStart
                self._debug_log(f"BacktestStart: {self.BacktestStart} -> UTC (preserved): {self._BacktestStartUtc}")
        else:
            self._BacktestStartUtc = datetime.min
        
        if hasattr(self, 'BacktestEnd') and self.BacktestEnd != datetime.max:
            # Check if time components are set (not midnight)
            if self.BacktestEnd.hour == 0 and self.BacktestEnd.minute == 0 and self.BacktestEnd.second == 0 and self.BacktestEnd.microsecond == 0:
                # Date only - treat as inclusive end date (include all of that day)
                # Convert to next day 00:00:00 UTC (exclusive) to include all of the specified date
                # Example: BacktestEnd = 03.12.2025 -> _BacktestEndUtc = 04.12.2025 00:00:00 UTC (includes all of Dec 3)
                next_day = self.BacktestEnd + timedelta(days=1)
                self._BacktestEndUtc = self._convert_date_to_utc_midnight(next_day)
                self._debug_log(f"BacktestEnd: {self.BacktestEnd} (inclusive date) -> UTC next day 00:00 (exclusive): {self._BacktestEndUtc}")
            else:
                # Has time components - use as-is (assumed to be UTC, exclusive)
                self._BacktestEndUtc = self.BacktestEnd
                self._debug_log(f"BacktestEnd: {self.BacktestEnd} (exclusive) -> UTC (preserved): {self._BacktestEndUtc}")
        else:
            self._BacktestEndUtc = datetime.max

        # call robot's OnInit
        self._debug_log("[DEBUG KitaApi.do_init] Calling robot.on_init()...")
        self.robot.on_init()  # type: ignore
        self._debug_log("[DEBUG KitaApi.do_init] robot.on_init() completed")

    WarmupStart: datetime = datetime.min # Explicit warmup start date

    def prepare_backtest(self):
        """
        Finalize warm-up period and load data.
        Should be called after indicators are created (usually at end of do_start).
        """
        if self._prepared:
            return
        
        # User specified WarmupStart logic
        if self.WarmupStart != datetime.min:
             self.AllDataStartUtc = self._convert_date_to_utc_midnight(self.WarmupStart)
             self._debug_log(f"Using manual WarmupStart: {self.WarmupStart} -> UTC: {self.AllDataStartUtc}")
        elif self._BacktestStartUtc != datetime.min:
             # Fallback if no warmup specified: start at backtest start (0 warmup)
             self.AllDataStartUtc = self._BacktestStartUtc
             self._debug_log(f"No WarmupStart specified, using BacktestStart: {self.AllDataStartUtc}")
        
        # Set AllDataEndUtc if not explicitly set
        if getattr(self, 'AllDataEndUtc', datetime.max) == datetime.max:
            if self._BacktestEndUtc != datetime.max:
                self.AllDataEndUtc = self._BacktestEndUtc
        
        # load bars and data rate
        self._debug_log(f"[DEBUG prepare_backtest] Loading data for {len(self.symbol_dictionary)} symbol(s)...")
        for symbol in self.symbol_dictionary.values():
            self._debug_log(f"[DEBUG prepare_backtest] Checking historical data for {symbol.name}...")
            symbol.check_historical_data()  # make sure data do exist since AllDataStartUtc
            self._debug_log(f"[DEBUG prepare_backtest] Making time aware for {symbol.name}...")
            symbol.make_time_aware()  # make sure all start/end datetimes are time zone aware
            self._debug_log(f"[DEBUG prepare_backtest] Loading datarate and bars for {symbol.name}...")
            symbol.load_datarate_and_bars()
            self._debug_log(f"[DEBUG prepare_backtest] Completed loading for {symbol.name}")
        
        self._prepared = True

    def do_start(self):
        for symbol in self.symbol_dictionary.values():
            self.robot.on_start(symbol)  # type: ignore
        
        # Finalize and load data now that all indicators are created
        self.prepare_backtest()

    def do_tick(self):
        # Update quote, bars, indicators, account, bot
        # 1st tick must update all bars and Indicators which have been inized in on_init()
        for symbol in self.symbol_dictionary.values():
            # Track bar counts and bar times BEFORE symbol_on_tick() is called (to detect new bars)
            if not hasattr(symbol, '_previous_bar_counts'):
                symbol._previous_bar_counts = {}
            if not hasattr(symbol, '_previous_bar_times'):
                symbol._previous_bar_times = {}
            previous_counts = {}
            previous_bar_times = {}
            for bars in symbol.bars_dictonary.values():
                bars_id = id(bars)
                previous_counts[bars_id] = bars.count
                # Track the last bar time for each timeframe (to detect new bars when ring buffer is full)
                if bars.count > 1:
                    try:
                        prev_bar = bars.Last(1)  # Previous closed bar
                        if prev_bar:
                            previous_bar_times[bars_id] = prev_bar.OpenTime
                    except:
                        previous_bar_times[bars_id] = None
                else:
                    previous_bar_times[bars_id] = None
            
            # Update quote, bars, indicators which are bound to this symbol
            # This builds bars and updates indicators during warm-up phase
            error = symbol.symbol_on_tick()
            
            # Compare symbol.time (UTC) directly with _BacktestEndUtc (UTC) to avoid timezone conversion issues
            # symbol.time is in UTC from tick data, so compare with UTC end time
            if "" != error:
                self._debug_log(f"[do_tick] symbol_on_tick returned error: {error}")
            if symbol.time > self._BacktestEndUtc:
                self._debug_log(f"[do_tick] Stopping: symbol.time ({symbol.time}) > _BacktestEndUtc ({self._BacktestEndUtc})")
            if self._stop_requested:
                self._debug_log(f"[do_tick] Stopping: _stop_requested is True")
            
            if "" != error or symbol.time > self._BacktestEndUtc or self._stop_requested:
                return True  # end reached

            # Check if a new bar was created for any timeframe (compare with previous_counts tracked BEFORE symbol_on_tick)
            new_bar_created = False
            new_h4_bar_created = False  # Track if H4 bar (14400 seconds) was created
            new_m1_bar_created = False  # Track if M1 bar (60 seconds) was created
            new_h1_bar_created = False  # Track if H1 bar (3600 seconds) was created
            if len(previous_counts) == 0:
                self._debug_log(f"[do_tick] WARNING: previous_counts is empty! bars_dictonary has {len(symbol.bars_dictonary)} entries")
            else:
                for bars_id, prev_count in previous_counts.items():
                    bars = None
                    for symbol_bars in symbol.bars_dictonary.values():
                        if id(symbol_bars) == bars_id:
                            bars = symbol_bars
                            break
                    
                    if bars:
                        # Check if count increased OR bar time changed (for ring buffer when full)
                        current_bar_time = None
                        if bars.count > 1:
                            try:
                                prev_bar = bars.Last(1)  # Previous closed bar
                                if prev_bar:
                                    current_bar_time = prev_bar.OpenTime
                            except:
                                pass
                        
                        prev_bar_time = previous_bar_times.get(bars_id)
                        
                        if bars.count > prev_count:
                            # Count increased - definitely a new bar
                            new_bar_created = True
                            self._debug_log(f"[do_tick] New bar created: timeframe_seconds={bars.timeframe_seconds}, count={bars.count}, prev_count={prev_count}, symbol.time={symbol.time}, BacktestStartUtc={self._BacktestStartUtc}")
                            # Track which timeframe created a new bar
                            if bars.timeframe_seconds == 60:
                                new_m1_bar_created = True
                            elif bars.timeframe_seconds == 3600:
                                new_h1_bar_created = True
                            elif bars.timeframe_seconds == 14400:
                                new_h4_bar_created = True
                        elif prev_bar_time is not None and current_bar_time is not None and current_bar_time != prev_bar_time:
                            # Ring buffer is full (count == size), but bar time changed - new bar overwrote oldest
                            new_bar_created = True
                            self._debug_log(f"[do_tick] New bar created (ring buffer full): timeframe_seconds={bars.timeframe_seconds}, count={bars.count}, prev_count={prev_count}, current_bar_time={current_bar_time}, prev_bar_time={prev_bar_time}, symbol.time={symbol.time}")
                            # Track which timeframe created a new bar
                            if bars.timeframe_seconds == 60:
                                new_m1_bar_created = True
                            elif bars.timeframe_seconds == 3600:
                                new_h1_bar_created = True
                            elif bars.timeframe_seconds == 14400:
                                new_h4_bar_created = True
                        elif bars.count < prev_count:
                            self._debug_log(f"[do_tick] WARNING: bars.count ({bars.count}) < prev_count ({prev_count}) for timeframe_seconds={bars.timeframe_seconds}")
                        # Don't break here - we need to check all bars to find H4 bars
                    else:
                        self._debug_log(f"[do_tick] WARNING: Could not find bars object with id={bars_id}")

            # During warm-up phase, only build bars and update indicators, skip OnTick
            if symbol.is_warm_up:
                symbol.prev_time = symbol.time
                symbol.prev_bid = symbol.bid
                symbol.prev_ask = symbol.ask
                # Update tracked counts and bar times even during warm-up
                for bars in symbol.bars_dictonary.values():
                    bars_id = id(bars)
                    symbol._previous_bar_counts[bars_id] = bars.count
                    if bars.count > 1:
                        try:
                            prev_bar = bars.Last(1)
                            if prev_bar:
                                symbol._previous_bar_times[bars_id] = prev_bar.OpenTime
                            else:
                                symbol._previous_bar_times[bars_id] = None
                        except:
                            symbol._previous_bar_times[bars_id] = None
                    else:
                        symbol._previous_bar_times[bars_id] = None
                continue  # Skip OnTick and account updates during warm-up

            # Only call on_tick() when current time >= BacktestStart (not based on bar time)
            # The user's on_tick() will handle logging after it's called
            if symbol.time < self._BacktestStartUtc:
                symbol.prev_time = symbol.time
                symbol.prev_bid = symbol.bid
                symbol.prev_ask = symbol.ask
                # Update tracked counts and bar times
                for bars in symbol.bars_dictonary.values():
                    bars_id = id(bars)
                    symbol._previous_bar_counts[bars_id] = bars.count
                    if bars.count > 1:
                        try:
                            prev_bar = bars.Last(1)
                            if prev_bar:
                                symbol._previous_bar_times[bars_id] = prev_bar.OpenTime
                            else:
                                symbol._previous_bar_times[bars_id] = None
                        except:
                            symbol._previous_bar_times[bars_id] = None
                    else:
                        symbol._previous_bar_times[bars_id] = None
                continue  # Skip OnTick if current time is before start date
            
            # Update tracked counts and bar times AFTER checking (so next tick can compare)
            for bars in symbol.bars_dictonary.values():
                bars_id = id(bars)
                symbol._previous_bar_counts[bars_id] = bars.count
                # Update the last bar time for each timeframe
                if bars.count > 1:
                    try:
                        prev_bar = bars.Last(1)  # Previous closed bar
                        if prev_bar:
                            symbol._previous_bar_times[bars_id] = prev_bar.OpenTime
                        else:
                            symbol._previous_bar_times[bars_id] = None
                    except:
                        symbol._previous_bar_times[bars_id] = None
                else:
                    symbol._previous_bar_times[bars_id] = None

            # Call OnTick based on mode:
            # - For tick data (data_rate == 0): Call on_tick for every tick after BacktestStart
            # - For bar data: Call on_tick only when a new bar is created
            should_call_ontick = False
            if symbol.quote_provider.data_rate == 0:
                # Tick mode: call on_tick for every tick within BacktestStart/BacktestEnd range
                # Note: Filtering for unchanged prices happens "under the hood" in symbol_on_tick
                # Here we only check the timestamp range - user's on_tick is only called for ticks in range
                if symbol.time >= self._BacktestStartUtc and symbol.time < self._BacktestEndUtc:
                    should_call_ontick = True
                    self._debug_log(f"[do_tick] Calling on_tick (tick mode): symbol.time={symbol.time}, BacktestStartUtc={self._BacktestStartUtc}, BacktestEndUtc={self._BacktestEndUtc}")
            elif (new_m1_bar_created or new_h1_bar_created or new_h4_bar_created) and symbol.time >= self._BacktestStartUtc:
                # Bar mode: call on_tick only when a new bar is created
                should_call_ontick = True
                self._debug_log(f"[do_tick] Calling on_tick (bar mode): new_m1={new_m1_bar_created}, new_h1={new_h1_bar_created}, new_h4={new_h4_bar_created}, symbol.time={symbol.time}, BacktestStartUtc={self._BacktestStartUtc}")
            
            if should_call_ontick:
                # Update Account
                if len(self.positions) >= 1:
                    symbol.trade_provider.update_account()

                # Print OnTick date message when new day arrives and measure per-day performance
                import sys
                current_date_str = symbol.time.strftime("%d.%m.%Y")
                
                if self._last_ontick_date is None or self._last_ontick_date != current_date_str:
                    # OnTick date message goes to debug log, not stdout/stderr
                    self._debug_log(f"OnTick {current_date_str}")
                    self._last_ontick_date = current_date_str

                # call the robot
                self.robot.on_tick(symbol)  # type: ignore
            elif (new_m1_bar_created or new_h1_bar_created or new_h4_bar_created) and symbol.time < self._BacktestStartUtc:
                self._debug_log(f"[do_tick] Skipping on_tick (warm-up): new_m1={new_m1_bar_created}, new_h1={new_h1_bar_created}, new_h4={new_h4_bar_created}, symbol.time={symbol.time}, BacktestStartUtc={self._BacktestStartUtc}")
            elif not new_bar_created:
                # No new bar, but still update account if needed (for positions)
                if len(self.positions) >= 1:
                    symbol.trade_provider.update_account()

            # do max/min calcs
            # region
            self.max_margin = max(self.max_margin, self.account.margin)
            if len(self.positions) > self.same_time_open:
                self.same_time_open = len(self.positions)
                self.same_time_open_date_time = symbol.time
                self.same_time_open_count = len(self.history)

            self.max_balance = max(self.max_balance, self.account.balance)
            if self.max_balance - self.account.balance > self.max_balance_drawdown_value:
                self.max_balance_drawdown_value = self.max_balance - self.account.balance
                self.max_balance_drawdown_time = symbol.time
                self.max_balance_drawdown_count = len(self.history)

            self.max_equity = max(self.max_equity, self.account.equity)
            if self.max_equity - self.account.equity > self.max_equity_drawdown_value:
                self.max_equity_drawdown_value = self.max_equity - self.account.equity
                self.max_equity_drawdown_time = symbol.time
                self.max_equity_drawdown_count = len(self.history)
            # endregion

            symbol.prev_time = symbol.time
            symbol.prev_bid = symbol.bid
            symbol.prev_ask = symbol.ask

        return False

    def do_stop(self):
        """Stop the robot and close debug log file"""
        if self._debug_log_file:
            self._debug_log("KitaApi.do_stop() called")
            self._debug_log_file.close()
            self._debug_log_file = None
        for symbol in self.symbol_dictionary.values():
            self.robot.on_stop(symbol)  # type: ignore

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
            if symbol.time is None or symbol.time == datetime.min or (hasattr(symbol.time, 'tzinfo') and symbol.time.tzinfo is None):
                trading_days = 0
            else:
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
        max_current_equity_dd_percent = 100 * self.max_equity_drawdown_value / self.max_equity if self.max_equity > 0 else 0.0
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
            + CoFu.double_to_string(profit + loss, 2)
            + ", Long:,"
            + CoFu.double_to_string(
                sum(x.net_profit for x in self.history if x.trade_type == TradeType.Buy),
                2,
            )
            + ", Short:,"
            + CoFu.double_to_string(
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

        # log_text += ("max_margin: " + self.account.asset + " " + CoFu.double_to_string(mMaxMargin, 2) + "\n")
        # log_text += ("max_same_time_open: " + str(mSameTimeOpen + "\n")
        # + ", @ " + mSameTimeOpenDateTime.strftime("%d.%m.%Y %H:%M:%S")
        # + ", Count# " + str(mSameTimeOpenCount))
        log_text += (
            "Max Balance Drawdown Value: "
            + self.account.currency
            + " "
            + CoFu.double_to_string(self.max_balance_drawdown_value, 2)
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
                else CoFu.double_to_string(100 * self.max_balance_drawdown_value / self.max_balance, 2)
            )
            + "\n"
        )

        log_text += (
            "Max Equity Drawdown Value: "
            + self.account.currency
            + " "
            + CoFu.double_to_string(self.max_equity_drawdown_value, 2)
            + "; @ "
            + self.max_equity_drawdown_time.strftime("%d.%m.%Y %H:%M:%S")
            + "; Count# "
            + str(self.max_equity_drawdown_count)
            + "\n"
        )

        log_text += (
            "Max Current Equity Drawdown %: " + CoFu.double_to_string(max_current_equity_dd_percent, 2) + "\n"
        )

        log_text += "Max start Equity Drawdown %: " + CoFu.double_to_string(max_start_equity_dd_percent, 2) + "\n"

        log_text += (
            "Profit Factor: " + ("-" if losing_trades == 0 else CoFu.double_to_string(profit_factor, 2)) + "\n"
        )

        log_text += "Sharpe Ratio: " + CoFu.double_to_string(sharpe_ratio, 2) + "\n"
        log_text += "Sortino Ratio: " + CoFu.double_to_string(sortino_ratio, 2) + "\n"
        log_text += "Calmar Ratio: " + CoFu.double_to_string(calmar, 2) + "\n"
        log_text += "Winning Ratio: " + CoFu.double_to_string(winning_ratio_percent, 2) + "\n"
        log_text += "Trades Per Month: " + CoFu.double_to_string(trades_per_month, 2) + "\n"
        log_text += "Average Annual Profit Percent: " + CoFu.double_to_string(annual_profit_percent, 2) + "\n"

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
        #         log_text += ("histo_rest_quotient: " + CoFu.double_to_string(m_histo_rest_quotient = investCountHisto[1] / histoRestSum,
        # Stats printed to log file only - stdout removed
        self.log_add_text_line(log_text)
        self.log_close()

    def calculate_reward(self) -> float:
        return self.robot.get_tick_fitness()  # type:ignore

    # endregion


# end of file