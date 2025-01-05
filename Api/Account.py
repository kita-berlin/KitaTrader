from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Api.KitaApi import KitaApi


class Account:
    balance: float = 0
    margin: float = 0
    free_margin: float = 0
    margin_level: float = 0
    unrealized_net_profit: float = 0
    leverage: float = 0
    stop_out_level: float = 0
    currency: str = ""
    # total_margin_calculation_type:MarginMode
    # credit = account_info.credit
    # user_nick_name = account_info.name

    @property
    def equity(self) -> float:
        profit: float = 0
        for pos in self.api.positions:
            profit += pos.net_profit
        return self.api.account.balance + profit

    def __init__(self, api: KitaApi):
        self.api = api
        pass


# end of file
