from datetime import datetime
from Api.KitaApiEnums import *
from Api.Symbol import Symbol


class LogParams:
    def __init__(self):
        self.symbol: Symbol
        self.lots: float
        self.volume_in_units: float
        self.balance: float
        self.minlots: float
        self.trade_margin: float
        self.account_margin: float
        self.trade_type: TradeType
        self.entry_time: datetime
        self.closing_time: datetime
        self.entry_price: float
        self.closing_price: float
        self.comment: str
        self.commissions: float
        self.swap: float
        self.net_profit: float
        self.max_equity_drawdown: float
        self.max_trade_equity_drawdown_value: float


# end of file
