from enum import Enum


class TradeResult:
    """
    The result of a trade operation.
    """

    def __init__(
        self, is_successful=True, error=None, Position=None, PendingOrder=None
    ):
        self.is_successful = is_successful
        self.error = error
        self.Position = Position
        self.PendingOrder = PendingOrder

    def __str__(self):
        if self.is_successful:
            result = ["Success"]
            if self.Position:
                result.append(f"Position: PID{self.Position.id}")
            if self.PendingOrder:
                result.append(f"PendingOrder: OID{self.PendingOrder.id}")
            return f"trade_result ({', '.join(result)})"
        else:
            return f"trade_result (Error: {self.error})"
