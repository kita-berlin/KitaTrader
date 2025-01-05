from datetime import datetime, timedelta
from Api.Position import Position
from Api.KitaApi import KitaApi
from Api.Symbol import Symbol
from Api.KitaApiEnums import TradeType


class HedgePosition:
    # Member variables
    # region
    main_id: str = "Main;"
    reverse_id: str = "Reverse;"
    main_freeze_id: str = "main_freeze;"
    weekend_freeze_id: str = "weekend_freeze;"
    main_position: Position = None  # type: ignore
    freeze_position: Position = None  # type: ignore
    is_profit_earned: bool = False
    freeze_open_bar_count: int = 0
    freeze_corrected_entry_price: float = 0
    main_margin_after_open: float = 0
    freeze_margin_after_open: float = 0
    freeze_profit_offset: float = 0
    freeze_price_offset: float = 0
    last_modified_time: datetime = datetime.min
    bot: KitaApi

    @property
    def profit(self) -> float:
        return round(
            self.main_position.net_profit + self.freeze_position.net_profit + self.freeze_profit_offset,
            2,
        )

    @property
    def max_volume(self) -> float:
        if self.main_position is not None and self.freeze_position is not None:  # type: ignore
            return max(
                self.main_position.volume_in_units,
                self.freeze_position.volume_in_units,
            )
        elif self.main_position is not None:  # type: ignore
            return self.main_position.volume_in_units
        elif self.freeze_position is not None:  # type: ignore
            return self.freeze_position.volume_in_units
        else:
            return 0

    # endregion

    def __init__(self, algo_api: KitaApi, symbol: Symbol, is_long: bool, label: str):
        self.bot = algo_api
        self.symbol = symbol
        self.is_long = is_long
        self.label = label

    def do_freeze_open(self, volume: float = 0) -> bool:
        if self.freeze_position is None:  # type: ignore
            return self.do_freeze(self.main_freeze_id, volume)
        else:
            return False

    def do_main_open(
        self,
        volume: float,
        inherited_freeze_price_offset: float = 0,
        label_ext: str = main_id,
    ) -> bool:
        if self.main_position is None:  # type: ignore
            self.main_position = self.symbol.trade_provider.execute_market_order(
                TradeType.Buy if self.is_long else TradeType.Sell,
                self.symbol.name,
                self.symbol.normalize_volume_in_units(volume),
                self.label + label_ext,
            )

            if self.main_position is not None:  # type: ignore
                pass
                self.main_margin_after_open = self.symbol.trade_provider.account.margin  # type:ignore
                self.freeze_price_offset = inherited_freeze_price_offset
                self.freeze_corrected_entry_price = self.main_position.entry_price  # type:ignore

        return self.main_position is not None  # type: ignore

    def do_main_close(
        self,
        min_open_duration: list[timedelta],
        avg_open_duration_sum: list[timedelta],
        open_duration_count: list[int],
        max_open_duration: list[timedelta],
        is_utc: bool = True,
    ) -> bool:
        result = False
        if self.main_position is not None:  # type: ignore
            result = self.bot.close_trade(
                self.main_position,
                self.main_margin_after_open,
                min_open_duration,
                avg_open_duration_sum,
                open_duration_count,
                max_open_duration,
                is_utc,
            )
            self.main_position = None  # type: ignore
        return result

    def do_modify_volume(self, volume: float, current_open_price: float) -> bool:
        self.last_modified_time = self.symbol.time
        self.freeze_corrected_entry_price = current_open_price
        if self.main_position is not None:  # type: ignore
            return self.main_position.modify_volume(volume).is_successful
        return False

        self.open_duration_count = [0] * 1  # arrays because of by reference
        self.min_open_duration = [timedelta.max] * 1
        self.avg_open_duration_sum = [timedelta.min] * 1
        self.max_open_duration = [timedelta.min] * 1

    def do_freeze_close(
        self,
        min_open_duration: list[timedelta],
        avg_open_duration_sum: list[timedelta],
        open_duration_count: list[int],
        max_open_duration: list[timedelta],
        is_utc: bool = True,
    ) -> bool:
        result = False
        if self.freeze_position is not None:  # type: ignore
            self.freeze_profit_offset += self.freeze_position.net_profit
            self.freeze_price_offset += self.freeze_position.current_price - self.freeze_position.entry_price
            result = self.bot.close_trade(
                self.freeze_position,
                self.freeze_margin_after_open,
                min_open_duration,
                avg_open_duration_sum,
                open_duration_count,
                max_open_duration,
                is_utc,
            )
            self.freeze_position = None  # type: ignore
        return result

    def do_exchange_and_freeze_close(
        self,
        min_open_duration: list[timedelta],
        avg_open_duration_sum: list[timedelta],
        open_duration_count: list[int],
        max_open_duration: list[timedelta],
        is_utc: bool = True,
    ) -> bool:
        result = False
        if self.freeze_position is not None:  # type: ignore
            self.freeze_price_offset += self.freeze_position.current_price - self.freeze_position.entry_price
            self.exchange()
            self.freeze_profit_offset += self.freeze_position.net_profit
            result = self.bot.close_trade(
                self.freeze_position,
                self.freeze_margin_after_open,
                min_open_duration,
                avg_open_duration_sum,
                open_duration_count,
                max_open_duration,
                is_utc,
            )
            self.freeze_position = None  # type: ignore
        return result

    def do_both_close(
        self,
        min_open_duration: list[timedelta],
        avg_open_duration_sum: list[timedelta],
        open_duration_count: list[int],
        max_open_duration: list[timedelta],
        is_utc: bool = True,
    ) -> bool:
        if self.main_position is None and self.freeze_position is None:  # type: ignore
            return False

        if self.main_position is not None:  # type: ignore
            self.do_main_close(
                min_open_duration,
                avg_open_duration_sum,
                open_duration_count,
                max_open_duration,
                is_utc,
            )
            self.main_position = None  # type: ignore

        if self.freeze_position is not None:  # type: ignore
            self.do_freeze_close(
                min_open_duration,
                avg_open_duration_sum,
                open_duration_count,
                max_open_duration,
                is_utc,
            )
            self.freeze_position = None  # type: ignore

        return True

    def close_frozen_and_modify_main(
        self,
        volume: float,
        min_open_duration: list[timedelta],
        avg_open_duration_sum: list[timedelta],
        open_duration_count: list[int],
        max_open_duration: list[timedelta],
        is_utc: bool = True,
    ) -> bool:
        ret_val = False
        if self.main_position is None or self.freeze_position is None:  # type: ignore
            return ret_val

        self.main_position.modify_volume(volume)
        ret_val = self.do_freeze_close(
            min_open_duration,
            avg_open_duration_sum,
            open_duration_count,
            max_open_duration,
            is_utc,
        )
        self.freeze_position = None  # type: ignore

        return ret_val

    def close_main_and_modify_frozen(
        self,
        volume: float,
        min_open_duration: list[timedelta],
        avg_open_duration_sum: list[timedelta],
        open_duration_count: list[int],
        max_open_duration: list[timedelta],
        is_utc: bool = True,
    ) -> bool:
        ret_val = False
        if self.main_position is None or self.freeze_position is None:  # type: ignore
            return ret_val

        self.freeze_position.modify_volume(volume)
        ret_val = self.do_main_close(
            min_open_duration,
            avg_open_duration_sum,
            open_duration_count,
            max_open_duration,
            is_utc,
        )
        self.main_position = None  # type: ignore

        return ret_val

    def reverse(
        self,
        volume: float,
        min_open_duration: list[timedelta],
        avg_open_duration_sum: list[timedelta],
        open_duration_count: list[int],
        max_open_duration: list[timedelta],
        is_utc: bool = True,
    ) -> bool:
        ret_val = False
        if (
            self.main_position is None  # type: ignore
            and self.freeze_position is None  # type: ignore
            or self.main_position is not None  # type: ignore
            and self.freeze_position is not None  # type: ignore
        ):
            return ret_val

        if self.freeze_position is not None:  # type: ignore
            self.do_freeze_close(
                min_open_duration,
                avg_open_duration_sum,
                open_duration_count,
                max_open_duration,
                is_utc,
            )
            self.freeze_position = None  # type: ignore
        else:
            self.do_main_close(
                min_open_duration,
                avg_open_duration_sum,
                open_duration_count,
                max_open_duration,
                is_utc,
            )
            self.is_long = not self.is_long

        ret_val = self.do_main_open(volume, self.freeze_price_offset, self.reverse_id)
        return ret_val

    def exchange(self) -> bool:
        if self.main_position is None or self.freeze_position is None:  # type: ignore
            return False

        backup = self.main_position
        self.main_position = self.freeze_position
        self.freeze_position = backup

        return True

    def do_week_end_freeze(self, volume: float = 0) -> bool:
        if self.freeze_position is None:  # type: ignore
            return self.do_freeze(self.weekend_freeze_id, volume)
        else:
            return False

    def do_freeze(self, label_extension: str, volume: float) -> bool:
        result = None
        if self.freeze_position is None:  # type: ignore
            result = self.main_position.symbol.trade_provider.execute_market_order(
                TradeType.Buy if self.is_long else TradeType.Sell,
                self.symbol.name,
                self.symbol.normalize_volume_in_units(volume),
                self.label + label_extension,
            )

            if result is not None:  # type: ignore
                self.freeze_position = result
                self.freeze_margin_after_open = self.bot.account.margin
        return self.freeze_position is not None  # type: ignore


# end of file
