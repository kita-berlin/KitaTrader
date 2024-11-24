class LogParams:
    def __init__(self):
        self.symbol = None
        self.lots = 0.0
        self.initial_volume = 0.0
        self.minlots = 0.0
        self.trade_margin = 0.0
        self.account_margin = 0.0
        self.trade_type = None
        self.entry_time = None
        self.exit_time = None
        self.entry_price = 0.0
        self.closing_price = 0.0
        self.comment = ""
        self.commissions = 0.0
        self.swap = 0.0
        self.net_profit = 0.0
        self.max_equity_drawdown = 0.0
        self.max_trade_equity_drawdown_value = 0.0
