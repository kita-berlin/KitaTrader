import importlib.util
import os
import importlib
from typing import Tuple, Optional
from datetime import datetime, timezone
import math
import uuid
from typing import Dict
from tzlocal import get_localzone
import pytz
from ConvertUtils import ConvertUtils
from LogParams import LogParams
from Position import Position
from KitaSymbol import Symbol
from Account import Account
from Chart import Chart
from PyLogger import PyLogger
from MarketData import MarketDataParent
from QuoteProviders.QuoteProviderCsv import QuoteProvider
from TradingLoop import TradingLoop  # pylint: disable=import-error
from Quantrobot import Quantrobot
from TradeResult import TradeResult
from AlgoApiEnums import *
from CoFu import *


class AlgoApi(MarketDataParent, TradingLoop, Quantrobot):
    # Members
    # region
    bin_settings: BinSettings
    system_settings: SystemSettings
    symbol_dictionary: Dict[str, Symbol] = {}
    symbol_list: list[Symbol] = []
    positions: list[Position] = []
    history: list[Position] = []
    time: datetime
    max_equity_drawdown_value: float
    chart: Chart
    running_mode: RunningMode
    logger: PyLogger
    is_train: bool = False
    quote_provider: QuoteProvider
    # endregion

    def __init__(self):
        settings_path = os.path.join("Files", "System.json")
        error, self.system_settings = CoFu.load_settings(settings_path)
        if "" != error:
            # create empty sttings file
            self.system_settings = SystemSettings(
                "1",
                "2",
                "3",
                "4",
                "5",
                "6",
                "7",
                "8",
                "9",
                "10",
                "11",
                "12",
                "13",
                "14",
            )

        self.bin_settings = BinSettings(
            robot_name=self.system_settings.robot_name,
            default_symbol_name=self.system_settings.default_symbol_name,
            default_timeframe_seconds=self.get_timeframe_from_gui_params(self.system_settings),
            trade_direction=TradeDirection[self.system_settings.trade_direction],
            init_balance=float(self.system_settings.init_balance),
            start_dt=(datetime.strptime(self.system_settings.start_dt, "%Y-%m-%d")).replace(
                tzinfo=timezone.utc
            ),
            end_dt=(datetime.strptime(self.system_settings.end_dt, "%Y-%m-%d")).replace(
                tzinfo=timezone.utc
            ),
            is_visual_mode=self.system_settings.is_visual_mode == "True",
            speed=int(self.system_settings.speed),
            bars_in_chart=int(self.system_settings.chart_bars),
            data_rate=DataRates[self.system_settings.data_rate],
            platform=Platform[self.system_settings.platform],
            platform_parameter=self.system_settings.platform_parameter,
        )

        MarketDataParent.__init__(self)
        TradingLoop.__init__(self)
        Quantrobot.__init__(self)

        self.loaded_robot = self.load_class_from_file(
            os.path.join("robots", self.system_settings.robot_name + ".py"),
            self.system_settings.robot_name,
        )
        self.loaded_robot.__init__(self)
        self.Account = Account(self.bin_settings)
        pass

    # Method to dynamically load a class from a file
    def load_class_from_file(self, file_path, class_name):
        # Load the module dynamically
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is not None:
            module = importlib.util.module_from_spec(spec)
            if spec.loader is not None:
                spec.loader.exec_module(module)

        # Retrieve the class from the module
        if hasattr(module, class_name):
            return getattr(module, class_name)
        else:
            raise AttributeError(f"Class {class_name} not found in {file_path}")

    def get_timeframe_from_gui_params(self, system_settings):
        value = int(system_settings.default_timeframe_value)
        tf = TimeframeUnits[self.system_settings.default_timeframe_unit]
        ret_val = value
        if TimeframeUnits.Min == tf:
            ret_val = value * 60
        elif TimeframeUnits.Hour == tf:
            ret_val = value * 3600
        elif TimeframeUnits.Day == tf:
            ret_val = value * 3600 * 24
        elif TimeframeUnits.Week == tf:
            ret_val = value * 3600 * 24 * 7
        return ret_val

    # Trading API
    # region
    ###################################
    def get_symbol(self, symbolName):
        ret_val = Symbol(self, symbolName)
        self.symbol_dictionary[symbolName] = ret_val
        self.symbol_list.append(ret_val)
        return ret_val

    ###################################
    def close_trade(
        self,
        pos,
        marginAfterOpen,
        min_open_duration,
        avg_open_duration_sum,
        open_duration_count,
        max_open_duration,
        is_utc=True,
    ):
        close_result = self.close_position(pos)
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
            log.balance = self.Account.balance
            log.trade_margin = last_hist.margin
            log.max_equity_drawdown = self.max_equity_drawdown_value[0]
            # log.max_trade_equity_drawdown_value = self.max_trade_equity_drawdown_value[0]

            self.log_closing_trade(log)
            self.log_flush

            duration = last_hist.closing_time - last_hist.entry_time  # .seconds
            self.min(min_open_duration, duration)
            avg_open_duration_sum[0] += duration.seconds
            open_duration_count[0] += 1
            self.max(max_open_duration, duration)

            return True
        return False

    ###################################
    def execute_market_order(
        self, trade_type: TradeType, symbol_name: str, volume: float, label: str = ""
    ) -> Position:
        is_append_position = True  # default for Platform.MeFiles

        pos = Position()
        pos.symbol_name = symbol_name
        pos.symbol = self.symbol_dictionary[symbol_name]
        pos.trade_type = trade_type
        pos.volume_in_units = volume
        pos.quantity = volume / pos.symbol.lot_size
        pos.entry_time = self.time
        pos.entry_price = (
            pos.symbol.ask if TradeType.Buy == trade_type else pos.symbol.bid
        )
        pos.label = label
        pos.margin = volume * pos.entry_price / pos.symbol.leverage
        self.Account.margin += pos.margin

        if self.bin_settings.platform == Platform.Mt5Live:
            """
            # order_filling_fok = 0      # Fill Or Kill order
            # order_filling_ioc = 1      # Immediately Or Cancel
            # order_filling_return = 2      # Return remaining volume to book
            # order_filling_boc = 3      # Book Or Cancel order

            struct mql_trade_request
            {
               ENUM_TRADE_REQUEST_ACTIONS    action;           // trade operation type
               ulong                         magic;            // Expert Advisor ID (magic number)
               ulong                         order;            // Order ticket
               string                        symbol;           // trade symbol
               double                        volume;           // Requested volume for a deal in lots
               double                        price;            // Price
               double                        stoplimit;        // stop_limit level of the order
               double                        sl;               // stop Loss level of the order
               double                        tp;               // Take Profit level of the order
               ulong                         deviation;        // Maximal possible deviation from the requested price
               ENUM_ORDER_TYPE               type;             // Order type
               ENUM_ORDER_TYPE_FILLING       type_filling;     // Order execution type
               ENUM_ORDER_TYPE_TIME          type_time;        // Order expiration type
               datetime                      expiration;       // Order expiration time (for the orders of ORDER_TIME_SPECIFIED type)
               string                        comment;          // Order comment
               ulong                         Position;         // Position ticket
               ulong                         position_by;      // The ticket of an opposite Position
            };
            """
            import MetaTrader5 as mt5

            order = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol_name,
                "volume": volume / pos.symbol.lot_size,
                "type": (
                    mt5.ORDER_TYPE_BUY
                    if TradeType.Buy == trade_type
                    else TradeType.Sell
                ),
                "price": pos.entry_price,
                "deviation": 10,
                "type_filling": mt5.ORDER_FILLING_IOC,  # ORDER_FILLING_IOC ist the only one that works
            }

            """
            struct mql_trade_result
            {
               uint     retcode;          // Operation return code
               ulong    deal;             // Deal ticket, if it is performed
               ulong    order;            // Order ticket, if it is placed
               double   volume;           // Deal volume, confirmed by broker
               double   price;            // Deal price, confirmed by broker
               double   bid;              // Current bid price
               double   ask;              // Current ask price
               string   comment;          // Broker comment to operation (by default it is filled by description of trade server return code)
               uint     request_id;       // Request ID set by the terminal during the dispatch
               int      retcode_external; // Return code of an external trading system
            };
            """
            mql_trade_result = mt5.order_send(order)  # pylint: disable=no-member
            lastError, description = mt5.last_error()  # pylint: disable=no-member
            if 1 == lastError and "Request executed" in mql_trade_result.comment:
                pos.id = mql_trade_result.order
                mt5_pos = mt5.positions_get(ticket=pos.id)  # pylint: disable=no-member
                pos.volume_in_units = mt5_pos[0].volume * pos.symbol.lot_size
                pos.entry_time = datetime.fromtimestamp(mt5_pos[0].time)
                pos.entry_price = mt5_pos[0].price_open
                pos.margin = pos.volume_in_units * pos.entry_price / pos.symbol.leverage
                pass
            else:
                is_append_position = False
        pass

        if is_append_position:
            self.positions.append(pos)
        else:
            pos = None

        self.chart.draw_icon(
            str(uuid.uuid4()),
            (
                ChartIconType.UpArrow
                if trade_type == TradeType.Buy
                else ChartIconType.DownArrow
            ),
            pos.entry_time,
            pos.entry_price,
            "blue" if trade_type == TradeType.Buy else "red",
        )

        return pos

    ###################################
    def close_position(self, pos: Position):
        trade_result = TradeResult()
        try:
            if self.bin_settings.platform == Platform.Mt5Live:
                import MetaTrader5 as mt5

                symbol = self.symbol_dictionary[pos.symbol_name]
                mt5_tt = (
                    mt5.ORDER_TYPE_BUY
                    if TradeType.Sell == pos.trade_type
                    else mt5.ORDER_TYPE_SELL
                )
                exit_price = (
                    symbol.ask if TradeType.Buy == pos.trade_type else symbol.bid
                )
                order = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": pos.symbol_name,
                    "volume": pos.Quantity,
                    "type": mt5_tt,
                    "price": exit_price,
                    "deviation": 10,
                    "type_filling": mt5.ORDER_FILLING_IOC,  # ORDER_FILLING_IOC ist the only one that works
                }

                mql_trade_result = mt5.order_send(order)  # pylint: disable=no-member
                lastError, description = mt5.last_error()  # pylint: disable=no-member
                if 1 == lastError and "Request executed" in mql_trade_result.comment:
                    pass

            self.Account.margin -= pos.margin
            pos.closing_price = pos.current_price
            pos.closing_time = self.time
            self.history.append(pos)
            self.positions.remove(pos)
            self.Account.balance += pos.net_profit
            trade_result.is_successful = True
        except:
            pass

        return trade_result

    # endregion

    # Long/Short and other arithmetic
    # region
    def is_greater_or_equal_long(self, long_not_short, val1, val2):
        return val1 >= val2 if long_not_short else val1 <= val2

    def is_less_or_equal_long(self, long_not_short, val1, val2):
        return val1 <= val2 if long_not_short else val1 >= val2

    def is_greater_long(self, long_not_short, val1, val2):
        return val1 > val2 if long_not_short else val1 < val2

    def is_less_long(self, long_not_short, val1, val2):
        return val1 < val2 if long_not_short else val1 > val2

    def is_crossing(self, long_not_short, a_current, a_prev, b_current, b_prev):
        return self.is_greater_or_equal_long(
            long_not_short, a_current, b_current
        ) and self.is_less_or_equal_long(long_not_short, a_prev, b_prev)

    def add_long(self, long_not_short, val1, val2):
        return val1 + val2 if long_not_short else val1 - val2

    def sub_long(self, long_not_short, val1, val2):
        return val1 - val2 if long_not_short else val1 + val2

    def diff_long(self, long_not_short, val1, val2):
        return val1 - val2 if long_not_short else val2 - val1

    def i_price(self, dPrice, tickSize):
        return int(math.copysign(0.5 + abs(dPrice) / tickSize, dPrice))

    def d_price(self, price, tickSize):
        return tickSize * price

    def max(self, ref_value, compare):
        if compare > ref_value[0]:
            ref_value[0] = compare
            return True
        return False

    def min(self, ref_value, compare):
        if compare < ref_value[0]:
            ref_value[0] = compare
            return True
        return False

    def sharpe_sortino(self, isSortino, vals):
        if len(vals) < 2:
            return float("nan")

        average = sum(vals) / len(vals)
        sd = math.sqrt(
            sum((val - average) ** 2 for val in vals if not isSortino or val < average)
            / (len(vals) - 1)
        )
        return average / sd if sd != 0 else float("nan")

    def standard_deviation(self, isSortino, vals):
        average = sum(vals) / len(vals)
        return math.sqrt(
            sum((val - average) ** 2 for val in vals if not isSortino or val < average)
            / (len(vals) - 1)
        )

    def is_new_bar(self, seconds: int, time: datetime, prevTime: datetime) -> bool:
        if datetime.min == prevTime:
            return True
        return int(time.timestamp()) // seconds != int(prevTime.timestamp()) // seconds

    # endregion

    # Logging
    # region
    logging_trade_count = 0

    @property
    def is_open(self):
        return self.log_stream_writer is not None

    def open_logfile(
        self, logger, filename="", mode=LoggerConstants.HeaderAndSeveralLines, header=""
    ):
        if self.running_mode != RunningMode.Optimization:
            open_state = self.logger.log_open(
                self.logger.make_log_path(),
                filename,
                self.running_mode == RunningMode.RealTime,
                mode,
            )
            # if not openState:
            self.write_log_header(mode, header)

    def write_log_header(self, mode=LoggerConstants.HeaderAndSeveralLines, header=""):
        log_header = ""
        if (
            self.logger is None or not self.logger.is_open
        ):  # or int(LoggerConstants.no_header) & int(self.logger.mode) != 0:
            return

        self.logger.add_text("sep =,")  # Hint for Excel

        if LoggerConstants.SelfMade == mode:
            log_header = header
        else:
            log_header += (
                "\nOpenDate,OpenTime,symbol,Lots,open_price,Swap,Swap/Lot,open_asks,open_bid,open_spread_pts"
                if 0 == (self.logger.mode & LoggerConstants.OneLine)
                else ","
            )
            log_header += (
                ",CloseDate,ClosingTime,Mode,Volume,closing_price,commission,Comm/Lot,close_ask,close_bid,close_spread_pts"
                if 0 == (self.logger.mode & LoggerConstants.OneLine)
                else ","
            )
            log_header += ",Number,Dur. d.h.self.s,Balance,point_value,diff_pts,diff_gross,net_profit,net_prof/Lot,account_margin,trade_margin"
            # if 0 == (self.logger.mode & one_line) log_header += (",\n")

        self.logger.add_text(log_header)
        self.logger.flush()
        self.header_split = log_header.split(",")

    def log_add_text(self, s):
        if self.logger is None or not self.logger.is_open:
            return

        self.logger.add_text(s)

    def log_add_text_line(self, s):
        self.log_add_text(s + "\n")

    def log_closing_trade(self, lp):
        if self.logger is None or not self.logger.is_open:
            return

        # orgComment;123456,aaa,+-ppp     meaning:
        # openAskInPts,openSpreadInPts
        openBid, open_ask = 0, 0
        if lp.comment is not None:
            bid_asks = lp.comment.split(";")
            if len(bid_asks) >= 2:
                bid_asks = bid_asks[1].split(",")
                if len(bid_asks) == 2:
                    i_ask = ConvertUtils.string_to_integer(bid_asks[0])
                    open_ask = lp.symbol.tick_size * i_ask
                    open_bid = lp.symbol.tick_size * (
                        i_ask - ConvertUtils.string_to_integer(bid_asks[1])
                    )

        price_diff = (1 if lp.trade_type == TradeType.Buy else -1) * (
            lp.closing_price - lp.entry_price
        )
        point_diff = self.i_price(price_diff, lp.symbol.tick_size)
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
                self.logger.add_text(ConvertUtils.double_to_string(lp.Lots, lot_digits))
                continue
            elif change_part == "OpenPrice":
                self.logger.add_text(
                    ConvertUtils.double_to_string(lp.entry_price, lp.symbol.digits)
                )
                continue
            elif change_part == "Swap":
                self.logger.add_text(ConvertUtils.double_to_string(lp.Swap, 2))
                continue
            elif change_part == "Swap/Lot":
                self.logger.add_text(
                    ConvertUtils.double_to_string(lp.Swap / lp.Lots, 2)
                )
                continue
            elif change_part == "OpenAsks":
                self.logger.add_text(
                    ConvertUtils.double_to_string(open_ask, lp.symbol.digits)
                    if lp.trade_type == TradeType.Buy
                    else ""
                )
                continue
            elif change_part == "OpenBid":
                self.logger.add_text(
                    ConvertUtils.double_to_string(openBid, lp.symbol.digits)
                    if lp.trade_type == TradeType.Sell
                    else ""
                )
                continue
            elif change_part == "OpenSpreadPoints":
                self.logger.add_text(
                    ConvertUtils.double_to_string(
                        self.i_price((open_ask - openBid), lp.symbol.tick_size), 0
                    )
                )
                continue
            elif change_part == "CloseDate":
                self.logger.add_text(lp.closing_time.strftime("%Y.%m.%d"))
                continue
            elif change_part == "ClosingTime":
                self.logger.add_text(lp.closing_time.strftime("%H:%M:%S"))
                continue
            elif change_part == "Mode":
                self.logger.add_text(
                    "Short" if lp.trade_type == TradeType.Sell else "Long"
                )
                continue
            elif change_part == "PointValue":
                self.logger.add_text(
                    ConvertUtils.double_to_string(
                        self.calc_1point_and_1lot_2money(lp.symbol), 5
                    )
                )
                continue
            elif change_part == "ClosingPrice":
                self.logger.add_text(
                    ConvertUtils.double_to_string(lp.closing_price, lp.symbol.digits)
                )
                continue
            elif change_part == "Commission":
                self.logger.add_text(ConvertUtils.double_to_string(lp.commissions, 2))
                continue
            elif change_part == "Comm/Lot":
                self.logger.add_text(
                    ConvertUtils.double_to_string(lp.commissions / lp.Lots, 2)
                )
                continue
            elif change_part == "CloseAsk":
                self.logger.add_text(
                    "{:.{}f}".format(
                        self.get_bid_ask_price(lp.symbol, BidAsk.Ask), lp.symbol.digits
                    )
                    if lp.trade_type == TradeType.Sell
                    else ""
                )
                continue
            elif change_part == "CloseBid":
                self.logger.add_text(
                    ConvertUtils.double_to_string(
                        self.get_bid_ask_price(lp.symbol, BidAsk.Bid), lp.symbol.digits
                    )
                    if lp.trade_type == TradeType.Buy
                    else ""
                )
                continue
            elif change_part == "CloseSpreadPoints":
                self.logger.add_text(
                    ConvertUtils.double_to_string(
                        self.i_price(
                            self.get_bid_ask_price(lp.symbol, BidAsk.Ask)
                            - self.get_bid_ask_price(lp.symbol, BidAsk.Bid),
                            lp.symbol.tick_size,
                        ),
                        0,
                    )
                )
                continue
            elif change_part == "Balance":
                self.logger.add_text(ConvertUtils.double_to_string(lp.balance, 2))
                continue
            elif change_part == "Dur. d.h.self.s":
                self.logger.add_text(
                    str(lp.entry_time - lp.closing_time).rjust(11, " ")
                )
                continue
            elif change_part == "Number":
                self.logging_trade_count += 1
                self.logger.add_text(
                    ConvertUtils.integer_to_string(self.logging_trade_count)
                )
                continue
            elif change_part == "Volume":
                self.logger.add_text(
                    ConvertUtils.double_to_string(lp.volume_in_units, 1)
                )
                continue
            elif change_part == "DiffPoints":
                self.logger.add_text(ConvertUtils.double_to_string(point_diff, 0))
                continue
            elif change_part == "DiffGross":
                self.logger.add_text(
                    ConvertUtils.double_to_string(
                        self.calc_points_and_lot_2money(lp.symbol, point_diff, lp.Lots),
                        2,
                    )
                )
                continue
            elif change_part == "net_profit":
                self.logger.add_text(ConvertUtils.double_to_string(lp.net_profit, 2))
                continue
            elif change_part == "NetProf/Lot":
                self.logger.add_text(
                    ConvertUtils.double_to_string(lp.net_profit / lp.Lots, 2)
                )
                continue
            elif change_part == "AccountMargin":
                self.logger.add_text(
                    ConvertUtils.double_to_string(lp.account_margin, 2)
                )
                continue
            elif change_part == "TradeMargin":
                self.logger.add_text(ConvertUtils.double_to_string(lp.trade_margin, 2))
                continue
            elif change_part == "MaxEquityDrawdown":
                self.logger.add_text(
                    ConvertUtils.double_to_string(lp.max_equity_drawdown, 2)
                )
                continue
            elif change_part == "MaxTradeEquityDrawdownValue":
                self.logger.add_text(
                    ConvertUtils.double_to_string(lp.max_trade_equity_drawdown_value, 2)
                )
                continue
            else:
                pass

        self.logger.flush()

    def log_flush(self):
        if self.logger is None or not self.logger.is_open:
            return
        self.logger.flush()

    def log_close(self, header_line=""):
        if self.logger is None or not self.logger.is_open:
            return

        self.logger.close(header_line)
        self.log_stream_writer = None
        # endregion

    # Price and lot/volume calculation
    # region
    @staticmethod
    def get_bid_ask_price(symbol: Symbol, bidAsk):
        return symbol.bid if BidAsk == BidAsk.Bid else symbol.ask

    @staticmethod
    def calc_profitmode2_lots(
        symbol, profitMode, value, tpPts, riskPoints, desiMon, lotSiz
    ):
        desi_mon = 0
        lot_siz = 0

        if math.isnan(symbol.tick_value):
            return "Invalid tick_value"
        """
        if ProfitMode == ProfitMode.Lots:
            desi_mon = self.calc_points_and_lot_2money(symbol: Symbol, tpPts, lot_siz =value)
        elif ProfitMode == ProfitMode.lots_pro10k:
            lot_siz = (self.Account.balance - self.Account.margin) / 10000 * value
            desi_mon = self.calc_points_and_lot_2money(symbol: Symbol, tpPts, lotSiz)
        elif ProfitMode == ProfitMode.profit_percent:
            desi_mon = (self.Account.balance - self.Account.margin) * value / 100
            lot_siz = self.calc_money_and_points_2lots(symbol: Symbol, desiMon, tpPts, self.commission_per_lot(symbol: Symbol))
        elif ProfitMode == ProfitMode.profit_ammount:
            lot_siz = self.calc_money_and_points_2lots(symbol: Symbol, desi_mon =value, tp_pts =tpPts, x_pro_lot =self.commission_per_lot(symbol: Symbol))
        elif profitMode in [ProfitMode.risk_constant, ProfitMode.risk_reinvest]:
            balance = self.Account.balance if ProfitMode == ProfitMode.risk_reinvest else self.initial_account_balance
            money_to_risk = (balance - self.Account.margin) * value / 100
            lot_siz = self.calc_money_and_points_2lots(symbol: Symbol, moneyToRisk, riskPoints, self.commission_per_lot(symbol: Symbol))
            desi_mon = self.calc_points_and_lot_2money(symbol: Symbol, tpPts, lotSiz)
        elif profitMode in [ProfitMode.constant_invest, ProfitMode.Reinvest]:
            invest_money = (self.initial_account_balance if ProfitMode == ProfitMode.constant_invest else self.Account.balance) * value / 100
            units = investMoney * symbol.tick_size / symbol.tick_value / symbol.bid
            lot_siz = symbol.volume_in_units_to_quantity(units)
            desi_mon = self.calc_points_and_lot_2money(symbol: Symbol, tpPts, lotSiz)
        """
        return ""

    @staticmethod
    def calc_points_and_lot_2money(symbol: Symbol, points, lot):
        return symbol.tick_value * symbol.lot_size * points * lot

    @staticmethod
    def calc_points_and_volume_2money(symbol: Symbol, points, volume):
        return symbol.tick_value * points * volume / symbol.lot_size

    @staticmethod
    def calc_1point_and_1lot_2money(symbol: Symbol, reverse=False):
        ret_val = AlgoApi.calc_points_and_lot_2money(symbol, 1, 1)
        if reverse:
            ret_val *= symbol.bid
        return ret_val

    @staticmethod
    def calc_money_and_lot_2points(symbol: Symbol, money, lot):
        return money / (lot * symbol.tick_value * symbol.lot_size)

    @staticmethod
    def calc_money_and_volume_2points(symbol: Symbol, money, volume):
        return money / (volume * symbol.tick_value)

    @staticmethod
    def calc_money_and_points_2lots(symbol: Symbol, money, points, xProLot):
        ret_val = abs(money / (points * symbol.tick_value * symbol.lot_size + xProLot))
        ret_val = max(ret_val, symbol.min_lot(symbol))
        ret_val = min(ret_val, symbol.max_lot(symbol))
        return ret_val
        # endregion

    @staticmethod
    def get_utc_time_from_local_time(localTime: datetime) -> datetime:
        s_local_tz = get_localzone()
        local_time_with_tz = localTime.astimezone(s_local_tz)
        return local_time_with_tz.astimezone(pytz.utc)


# end of file