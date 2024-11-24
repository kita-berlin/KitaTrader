from datetime import datetime
from AlgoApiEnums import *


class Position:
    def __init__(self):
        self.symbol_name = ""
        self.trade_type = TradeType.buy
        self.volume_in_units = 0
        self.id = 0
        self.gross_profit = 0
        self.entry_price = 0
        self.stop_loss = 0
        self.take_profit_percent = 0
        # self.net_profit is a property
        self.swap = 0
        self.commissions = 0
        self.entry_time = datetime.min
        self.pips = 0
        self.label = ""
        self.comment = ""
        self.quantity = 0
        self.has_trailing_stop = False
        self.margin = 0
        # self.current_price is a property
        self.stop_loss_trigger_method = StopTriggerMethod.trade
        self.closing_price = 0
        self.max_drawdown = 0
        self.symbol = None

    def modify_stop_loss_price(self, stopLoss):
        """
        Shortcut for Robot.modify_position method to change the Stop Loss price.
        """
        pass

    def modify_take_profit_price(self, takeProfit):
        """
        Shortcut for Robot.modify_position method to change the Take Profit price.
        """
        pass

    def modify_stop_loss_pips(self, stopLossPips):
        """
        Shortcut for the Robot.modify_position method to change the Stop Loss in pips.
        """
        pass

    def modify_take_profit_pips(self, takeProfitPips):
        """
        Shortcut for the Robot.modify_position method to change the Take Profit in pips.
        """
        pass

    def modify_trailing_stop(self, hasTrailingStop):
        """
        Shortcut for the Robot.modify_position method to change the Trailing Stop.
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
        return self.symbol.bid if self.trade_type == TradeType.buy else self.symbol.ask

    @property
    def net_profit(self):
        if 0 == self.id:  # me_files and Mt5 backtest
            if 0 == self.closing_price:
                # Position still open and in Positions queue
                return (
                    (self.current_price - self.entry_price)
                    * (1 if self.trade_type == TradeType.buy else -1)
                    * self.volume_in_units
                )
            else:
                # Position closed and in History queue
                return (
                    (self.closing_price - self.entry_price)
                    * (1 if self.trade_type == TradeType.buy else -1)
                    * self.volume_in_units
                )
        else:  # Mt5 live
            import MetaTrader5 as mt5

            mt5_pos = mt5.positions_get(ticket=self.id)  # pylint: disable=no-member
            ret_val = mt5_pos[0].profit  # pylint: disable=no-member
            return ret_val

    pass


# end of file
