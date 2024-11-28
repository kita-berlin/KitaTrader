from AlgoApiEnums import *


class Account:
    type: AccountType
    balance: float
    equity: float
    margin: float
    free_margin: float
    margin_level: float
    unrealized_net_profit: float
    leverage: float
    stop_out_level: float
    asset: str
    # total_margin_calculation_type:MarginMode
    # credit = account_info.credit
    # user_nick_name = account_info.name

    def __init__(self):
        pass
