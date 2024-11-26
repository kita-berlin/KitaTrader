from datetime import datetime
from KitaSymbol import Symbol
from AlgoApiEnums import *


class Position:
    symbol_name: str = ""
    symbol: Symbol = None  # type: ignore
    trade_type: TradeType = TradeType.Buy
    volume_in_units: float = 0
    id: int = 0
    gross_profit: float = 0
    entry_price: float = 0
    stop_loss: float = 0
    # net_profit is a property
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
    # current_price is a property
    stop_loss_trigger_method: StopTriggerMethod = StopTriggerMethod.Trade
    closing_price: float = 0
    max_drawdown: float = 0

    def __init__(self):
        pass

    def modify_stop_loss_price(self, stopLoss):
        """
        Shortcut for Robot.modify_position method to change the stop Loss price.
        """
        pass

    def modify_take_profit_price(self, takeProfit):
        """
        Shortcut for Robot.modify_position method to change the Take Profit price.
        """
        pass

    def modify_stop_loss_pips(self, stopLossPips):
        """
        Shortcut for the Robot.modify_position method to change the stop Loss in Pips.
        """
        pass

    def modify_take_profit_pips(self, takeProfitPips):
        """
        Shortcut for the Robot.modify_position method to change the Take Profit in Pips.
        """
        pass

    def modify_trailing_stop(self, hasTrailingstop):
        """
        Shortcut for the Robot.modify_position method to change the Trailing stop.
        """
        pass

    def modify_volume(self, volume):
        """
        Shortcut for the Robot.modify_position method to change the volume_in_units.
        """
        pass

    def reverse(self, volume=None):
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
    def current_price(self):
        return self.symbol.Bid if self.trade_type == TradeType.Buy else self.symbol.Ask

    @property
    def net_profit(self):
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
            import MetaTrader5 as mt5

            mt5_pos = mt5.positions_get(ticket=self.id)  # pylint: disable=no-member
            ret_val = mt5_pos[0].profit  # pylint: disable=no-member
            return ret_val

    pass


# end of file
