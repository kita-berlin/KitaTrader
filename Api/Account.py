from AlgoApiEnums import *
from Settings import BinSettings
from CoFu import *


class Account:
    def __init__(self, bin_settings: BinSettings):
        if bin_settings.platform == Platform.Mt5Live:
            import MetaTrader5 as mt5
            account_info = mt5.account_info()  # pylint: disable=no-member
            self.account_type = AccountType.Hedged
            self.balance = account_info.balance
            self.equity = account_info.equity
            self.margin = account_info.margin
            self.free_margin = account_info.margin_free
            self.margin_level = account_info.margin_level
            # ACCOUNT_TRADE_MODE_DEMO, ACCOUNT_TRADE_MODE_CONTEST, ACCOUNT_TRADE_MODE_REAL
            self.is_live = 2 == account_info.trade_mode
            self.user_id = account_info.login
            self.number = account_info.login
            if "pepperstone" in account_info.company.lower():
                self.broker_symbol_name = "Pepperstone"
            if "raw" in account_info.company:
                self.broker_symbol_name = "Raw Trading Ltd"

            self.unrealized_net_profit = account_info.profit
            self.leverage = self.precise_leverage = account_info.leverage
            self.stop_out_level = account_info.margin_so_so
            self.asset = account_info.currency
            self.total_margin_calculation_type = account_info.margin_mode
            self.credit = account_info.credit
            self.user_nick_name = account_info.name

        if (
            bin_settings.platform == Platform.MeFiles
            or bin_settings.platform == Platform.Csv
            or bin_settings.platform == Platform.Mt5Backtest
        ):
            self.account_type = AccountType.Hedged
            self.balance = bin_settings.init_balance
            self.equity = bin_settings.init_balance
            self.margin = 0
            self.free_margin = bin_settings.init_balance
            # ACCOUNT_TRADE_MODE_DEMO, ACCOUNT_TRADE_MODE_CONTEST, ACCOUNT_TRADE_MODE_REAL
            self.is_live = 0
            self.margin_level = 0
            self.user_id = 2911
            self.number = 2911
            self.broker_symbol_name = "Pepperstone"

            self.unrealized_net_profit = 0
            self.leverage = self.precise_leverage = 500
            self.stop_out_level = 20
            self.asset = "EUR"
            self.total_margin_calculation_type = 0
            self.credit = 0
            self.user_nick_name = "MeFiles"
        pass
