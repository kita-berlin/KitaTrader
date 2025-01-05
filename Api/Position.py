from datetime import datetime
from Api.KitaApiEnums import TradeType, StopTriggerMethod
from Api.TradeResult import TradeResult


class Position:
    # Members
    # region
    symbol_name: str = ""
    from Api.Symbol import Symbol

    symbol: Symbol = None  # type: ignore
    trade_type: TradeType = TradeType.Buy
    volume_in_units: float = 0
    id: int = 0
    gross_profit: float = 0
    entry_price: float = 0
    stop_loss: float = 0
    swap: float = 0
    commissions: float = 0
    entry_time: datetime = datetime.min
    closing_time: datetime = datetime.min
    pips: float = 0
    label: str = ""
    comment: str = ""
    quantity: float = 0
    has_trailing_stop: bool = False
    margin: float = 0
    stop_loss_trigger_method: StopTriggerMethod = StopTriggerMethod.Trade
    closing_price: float = 0
    max_drawdown: float = 0
    # endregion

    def __init__(self):
        pass

    def modify_stop_loss_price(self, stopLoss: float):
        """
        Shortcut for Robot.modify_position method to change the stop Loss price.
        """
        pass

    def modify_take_profit_price(self, takeProfit: float):
        """
        Shortcut for Robot.modify_position method to change the Take Profit price.
        """
        pass

    def modify_stop_loss_pips(self, stopLossPips: float):
        """
        Shortcut for the Robot.modify_position method to change the stop Loss in Pips.
        """
        pass

    def modify_take_profit_pips(self, takeProfitPips: float):
        """
        Shortcut for the Robot.modify_position method to change the Take Profit in Pips.
        """
        pass

    def modify_trailing_stop(self, hasTrailingstop: bool):
        """
        Shortcut for the Robot.modify_position method to change the Trailing stop.
        """
        pass

    def modify_volume(self, volume: float) -> TradeResult:
        """
        Shortcut for the Robot.modify_position method to change the volume_in_units.
        """
        trade_result = TradeResult()
        trade_result.is_successful = True
        return trade_result
        pass

    def reverse(self, volume: float = None):  # type: ignore
        """
        Shortcut for the Robot.reverse_position method to change the direction of the trade.
        """
        pass

    def close(self):
        """
        Shortcut for the Robot.close_position method.
        """
        pass

    @property
    def current_price(self) -> float:
        return self.symbol.bid if self.trade_type == TradeType.Buy else self.symbol.ask

    @property
    def net_profit(self) -> float:
        if 0 == self.id:  # MeFiles and Mt5 backtest
            if 0 == self.closing_price:
                # Position still open and in Positions queue
                return (
                    (self.current_price - self.entry_price)
                    * (1 if self.trade_type == TradeType.Buy else -1)
                    * self.volume_in_units
                )
            else:
                # Position closed and in History queue
                return (
                    (self.closing_price - self.entry_price)
                    * (1 if self.trade_type == TradeType.Buy else -1)
                    * self.volume_in_units
                )
        else:  # Mt5 live
            # import MetaTrader5 as mt5

            # mt5_pos = mt5.positions_get(ticket=self.id)
            # ret_val = mt5_pos[0].profit
            # return ret_val
            return 0


# end of file
