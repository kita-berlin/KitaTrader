# from datetime import datetime
from Api.KitaApi import KitaApi, Symbol, Position, TradeType
from Api.TradeProvider import TradeProvider
from Api.TradeResult import TradeResult


class TradePaper(TradeProvider):
    def __init__(self, parameter: str = ""):
        TradeProvider.__init__(self, parameter)

    def init_symbol(self, api: KitaApi, symbol: Symbol, cache_path: str = ""):
        self.symbol = symbol
        self.api = api
        pass

    def update_account(self):
        pass

    def add_profit(self, profit: float):
        self.api.account.balance += profit

    def execute_market_order(
        self, trade_type: TradeType, symbol_name: str, volume: float, label: str = ""
    ) -> Position:
        is_append_position = True

        pos = Position()
        pos.symbol_name = symbol_name
        pos.symbol = self.api.symbol_dictionary[symbol_name]
        pos.trade_type = trade_type
        pos.volume_in_units = volume
        pos.quantity = volume / pos.symbol.lot_size
        pos.entry_time = pos.symbol.time
        pos.entry_price = pos.symbol.ask if TradeType.Buy == trade_type else pos.symbol.bid
        pos.label = label
        pos.margin = volume * pos.entry_price / pos.symbol.leverage
        self.api.account.margin += pos.margin

        if is_append_position:
            self.api.positions.append(pos)
        else:
            pos = None

        """
        self.chart.draw_icon(
            str(uuid.uuid4()),
            (
                ChartIconType.UpArrow
                if trade_type == TradeType.Buy
                else ChartIconType.DownArrow
            ),
            pos.entry_time,
            pos.entry_price,
            "blue" if trade_type == TradeType.Buy else "red",
        )
        """

        return pos  # type: ignore

    def close_position(self, pos: Position) -> TradeResult:
        trade_result = TradeResult()
        try:
            self.api.account.margin -= pos.margin
            pos.closing_price = pos.current_price
            pos.closing_time = pos.symbol.time
            self.api.history.append(pos)
            self.api.positions.remove(pos)
            pos.symbol.trade_provider.add_profit(pos.net_profit)
            trade_result.is_successful = True
        except:
            pass

        return trade_result
