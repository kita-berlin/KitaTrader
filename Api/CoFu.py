from enum import Enum
import json
import commentjson
from Settings import *


# Enums
# region
class TradeStates(Enum):
    long = 0
    short = 1
    flat = 2


class HighLow(Enum):
    high = 0
    low = 1


class TradeAction(Enum):
    open = 0
    close = 1


class BidAsk(Enum):
    bid = 0
    ask = 1


class ArithmeticOperators(Enum):
    min = 0
    max = 1
    greater = 2
    greater_equal = 3
    less = 4
    less_equal = 5
    equal = 6


class ProfitMode(Enum):
    lots = 0
    lots_pro10k = 1
    profit_percent = 2
    profit_ammount = 3
    risk_constant = 4
    risk_reinvest = 5
    constant_invest = 6
    reinvest = 7


class TradeDirection(Enum):
    long = 0
    short = 1
    both = 2
    both_in_one_bot = 3
    neither = 4
    mode1 = 5
    mode2 = 6
    mode3 = 7


class TimeframeUnits(Enum):
    sec = 0
    min = 1
    hour = 2
    day = 3
    week = 4


class PastFuture(Enum):
    past = 0
    future = 1


class PriceMode(Enum):
    value = 0
    previous = 1
    delta = 2


class IdfPathIndices(Enum):
    idf_ndx = 0
    pepper = 1
    pepper_commission = 2
    raw = 3  # IC Market raw trading
    raw_commission = 4
    dukas = 5
    dukas_commission = 6


class LoggerConstants(Enum):
    header_and_several_lines = 0
    no_header = 1  # must be binaries
    one_line = 2
    self_made = 4


class Platform(Enum):
    mt5_live = 0
    mt5_backtest = 1
    me_files = 2
    c_trader = 3
    csv = 4


class MovingAverageType(Enum):
    simple = 1
    exponential = 2
    TimeSeries = 3
    triangular = 4
    vidya = 5
    weighted = 6
    wilder_smoothing = 7
    hull = 8


class DataRates(Enum):
    ticks = 0
    m1 = 1
    default_timeframe = 2
    # endregion


################## Common Functions #################
class CoFu:
    ###################################
    @staticmethod
    def load_settings(path):
        try:
            with open(path, "r") as file:
                settings = commentjson.load(file)
                ret_val = SystemSettings(**settings)
                return "", ret_val

        except FileNotFoundError:
            return path + " not found", None

        except Exception as e:
            return "Fehler" + str(e), None

    ###################################
    @staticmethod
    def save_settings(path, parameter):
        try:
            with open(path, "w") as file:
                file.write(json.dumps(parameter.__dict__, indent=4))

        except Exception as e:
            pass


# end of file
