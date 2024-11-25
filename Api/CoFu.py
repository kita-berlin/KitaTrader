from enum import Enum
from typing import Tuple, Optional
import json
import commentjson
from Settings import *


# Enums
# region
class TradeStates(Enum):
    Long = 0
    Short = 1
    Flat = 2


class HighLow(Enum):
    High = 0
    Low = 1


class TradeAction(Enum):
    Open = 0
    Close = 1


class BidAsk(Enum):
    Bid = 0
    Ask = 1


class ArithmeticOperators(Enum):
    Min = 0
    Max = 1
    Greater = 2
    GreaterEqual = 3
    Less = 4
    LessEqual = 5
    Equal = 6


class ProfitMode(Enum):
    Lots = 0
    LotsPro10k = 1
    ProfitPercent = 2
    ProfitAmmount = 3
    RiskConstant = 4
    RiskReinvest = 5
    ConstantInvest = 6
    Reinvest = 7


class TradeDirection(Enum):
    Long = 0
    Short = 1
    Both = 2
    BothInOneBot = 3
    Neither = 4
    Mode1 = 5
    Mode2 = 6
    Mode3 = 7


class TimeframeUnits(Enum):
    Sec = 0
    Min = 1
    Hour = 2
    Day = 3
    Week = 4


class PastFuture(Enum):
    Past = 0
    Future = 1


class PriceMode(Enum):
    Value = 0
    Previous = 1
    Delta = 2


class IdfPathIndices(Enum):
    IdfNdx = 0
    Pepper = 1
    PepperCommission = 2
    Raw = 3  # IC Market raw trading
    RawCommission = 4
    Dukas = 5
    DukasCommission = 6


# must be binaries to be or'ed
class LoggerConstants(Enum):
    HeaderAndSeveralLines = 0
    NoHeader = 1
    OneLine = 2
    SelfMade = 4


class Platform(Enum):
    Mt5Live = 0
    Mt5Backtest = 1
    MeFiles = 2
    cTrader = 3
    Csv = 4


class MovingAverageType(Enum):
    Simple = 1
    Exponential = 2
    TimeSeries = 3
    Triangular = 4
    Vidya = 5
    Weighted = 6
    WilderSmoothing = 7
    Hull = 8


class DataRates(Enum):
    Ticks = 0
    M1 = 1
    Timeframe = 2
    # endregion


################## Common Functions #################
class CoFu:
    ###################################
    @staticmethod
    def load_settings(path) ->  Tuple[str, SystemSettings]:
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
