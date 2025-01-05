from abc import ABC, abstractmethod


class PendingOrder(ABC):
    """
    Provides access to properties of pending orders
    """

    @property
    @abstractmethod
    def symbol_code(self) -> str:
        """
        symbol code of the order
        """
        return ""

    #     @property
    #     @abstractmethod
    #     def trade_type(self) -> trade_type:
    #         """
    #         Specifies whether this order is to buy or sell.
    #         """
    #         pass

    #     @property
    #     @abstractmethod
    #     def volume(self) -> int:
    #         """
    #         Volume of this order.
    #         """
    #         pass

    #     @property
    #     @abstractmethod
    #     def initial_volume(self) -> float:
    #         """
    #         Volume of this order.
    #         """
    #         pass

    @property
    @abstractmethod
    def id(self) -> int:
        """
        Unique order Id.
        """
        pass

    # Pending order out commentet
    # region
    #     @property
    #     @abstractmethod
    #     def order_type(self) -> PendingOrder_type:
    #         """
    #         Specifies whether this order is stop or Limit.
    #         """
    #         pass

    #     @property
    #     @abstractmethod
    #     def target_price(self) -> float:
    #         """
    #         The order target price.
    #         """
    #         pass

    #     @property
    #     @abstractmethod
    #     def expiration_time(self) -> datetime:
    #         """
    #         The order Expiration time
    #         """
    #         return datetime.min

    #     @property
    #     @abstractmethod
    #     def stop_loss(self) -> float:
    #         """
    #         The order stop loss in price
    #         """
    #         pass

    #     @property
    #     @abstractmethod
    #     def stop_loss_pips(self) -> float:
    #         """
    #         The order stop loss in Pips
    #         """
    #         pass

    #     @property
    #     @abstractmethod
    #     def TakeProfitPercent(self) -> float:
    #         """
    #         The order take profit in price
    #         """

    #     @property
    #     @abstractmethod
    #     def take_profit_pips(self) -> float:
    #         """
    #         The order take profit in Pips
    #         """

    #     @property
    #     @abstractmethod
    #     def label(self) -> str:
    #         """
    #         User assigned identifier for the order.
    #         """
    #         return ""

    #     @property
    #     @abstractmethod
    #     def comment(self) -> str:
    #         """
    #         User assigned Order Comment
    #         """
    #         return ""

    #     @property
    #     @abstractmethod
    #     def quantity(self) -> float:
    #         """
    #         Quantity (lots) of this order
    #         """
    #         pass

    #     @property
    #     @abstractmethod
    #     def has_trailing_stop(self) -> bool:
    #         """
    #         When has_trailing_stop set to true, server updates stop Loss every time Position moves in your favor.
    #         """
    #         pass

    #     @property
    #     @abstractmethod
    #     def stop_loss_trigger_method(self) -> stop_trigger_method:
    #         """
    #         Trigger method for Position's stop_loss
    #         """
    #         pass

    #     @property
    #     @abstractmethod
    #     def stop_order_trigger_method(self) -> stop_trigger_method:
    #         """
    #         Determines how pending order will be triggered in case it's a stop_order
    #         """
    #         pass

    #     @property
    #     @abstractmethod
    #     def stop_limit_range_pips(self) -> float:
    #         """
    #         Maximum limit from order target price, where order can be executed.
    #         """
    #         pass

    #     # Obsolete. Use symbol.name instead
    #     # @property
    #     # @abstractmethod
    #     # def symbol_name(self) -> str:
    #     #     """
    #     #     Gets the symbol name.
    #     #     """
    #     #     pass

    #     @abstractmethod
    #     def modify_stop_loss_pips(self, stopLossPips: float]) -> trade_result:
    #         """
    #         Shortcut for Robot.modify_PendingOrder method to change stop Loss
    #         """
    #         pass

    #     @abstractmethod
    #     def modify_take_profit_pips(self, takeProfitPips: float]) -> trade_result:
    #         """
    #         Shortcut for Robot.modify_PendingOrder method to change Take Profit
    #         """
    #         pass

    #     @abstractmethod
    #     def modify_stop_limit_range(self, stopLimitRangePips: float) -> trade_result:
    #         """
    #         Shortcut for Robot.modify_PendingOrder method to change stop Limit Range
    #         """
    #         pass

    #     @abstractmethod
    #     def modify_expiration_time(self, expirationTime: datetime]) -> trade_result:
    #         """
    #         Shortcut for Robot.modify_PendingOrder method to change Expiration Time
    #         """
    #         pass

    #     @abstractmethod
    #     def modify_volume(self, volume: float) -> trade_result:
    #         """
    #         Shortcut for Robot.modify_PendingOrder method to change initial_volume
    #         """
    #         pass

    #     @abstractmethod
    #     def modify_target_price(self, targetPrice: float) -> trade_result:
    #         """
    #         Shortcut for Robot.modify_PendingOrder method to change Target Price
    #         """
    #         pass

    #     @abstractmethod
    #     def cancel(self) -> trade_result:
    #         """
    #         Shortcut for Robot.cancel_PendingOrder method
    #         """
    #         pass
    # endregion


# end of file
