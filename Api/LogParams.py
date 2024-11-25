from sympy import Symbol
from AlgoApiEnums import TradeType
from datetime import datetime


class LogParams:
    def __init__(self):
        self.symbol: Symbol
        self.lots: float
        self.initial_volume: float
        self.minlots: float
        self.trade_margin: float
        self.account_margin: float
        self.trade_type: TradeType
        self.entry_time: datetime
        self.exit_time: datetime
        self.entry_price: float
        self.closing_price: float
        self.comment: str
        self.commissions: float
        self.swap: float
        self.net_profit: float
        self.max_equity_drawdown: float
        self.max_trade_equity_drawdown_value: float
