import math
from AlgoApiEnums import *
from CoFu import *
from Position import Position


class HedgePosition:
    # Member variables
    # region
    main_id = "Main;"  # cannpt be defined in __init__ because needed in do_main_open(self, volume, inherited_freeze_price_offset =0, label_ext =main_id)
    reverse_id = "Reverse;"
    main_freeze_id = "main_freeze;"
    weekend_freeze_id = "weekend_freeze;"
    main_position: Position = None
    freeze_position: Position = None
    is_profit_earned: bool = False
    freeze_open_bar_count: int = 0
    freeze_corrected_entry_price: float = 0
    main_margin_after_open: float = 0
    freeze_margin_after_open: float = 0
    freeze_profit_offset: float = 0
    freeze_price_offset: float = 0

    @property
    def profit(self):
        return round(
            (0 if self.main_position is None else self.main_position.net_profit)
            + (0 if self.freeze_position is None else self.freeze_position.net_profit)
            + self.freeze_profit_offset,
            2,
        )

    @property
    def max_volume(self):
        if self.main_position is not None and self.freeze_position is not None:
            return max(
                self.main_position.initial_volume,
                self.freeze_position.initial_volume,
            )
        elif self.main_position is not None:
            return self.main_position.initial_volume
        elif self.freeze_position is not None:
            return self.freeze_position.initial_volume
        else:
            return 0

    # endregion

    def __init__(self, bot, symbol, is_long, label):
        self.bot = bot
        self.symbol = symbol
        self.is_long = is_long
        self.label = label

    def do_freeze_open(self, volume=0):
        if self.freeze_position is None:
            return self.do_freeze(self.main_freeze_id, volume)
        else:
            return False

    def do_main_open(self, volume, inherited_freeze_price_offset=0, label_ext=main_id):
        if self.main_position is None:
            self.main_position = self.bot.execute_market_order(
                TradeType.buy if self.is_long else TradeType.sell,
                self.symbol.name,
                self.symbol.normalize_volume_in_units(volume),
                self.label + label_ext,
            )

            if self.main_position is not None:
                self.main_margin_after_open = self.bot.Account.margin
                self.freeze_price_offset = inherited_freeze_price_offset
                self.freeze_corrected_entry_price = self.main_position.entry_price

        return self.main_position is not None

    def do_modify_volume(self, volume: float, current_open_price: float):
        #last_modified_time = self.time
        freeze_corrected_entry_price = current_open_price
        return self.main_position.modify_volume(volume).is_successful

    def do_main_close(
        self,
        min_open_duration,
        avg_open_duration_sum,
        open_duration_count,
        max_open_duration,
        is_utc=True,
    ):
        result = False
        if self.main_position is not None:
            result = self.bot.close_trade(
                self.main_position,
                self.main_margin_after_open,
                min_open_duration,
                avg_open_duration_sum,
                open_duration_count,
                max_open_duration,
                is_utc,
            )
            self.main_position = None
        return result

    def do_freeze_close(
        self,
        min_open_duration,
        avg_open_duration_sum,
        open_duration_count,
        max_open_duration,
        is_utc=True,
    ):
        result = False
        if self.freeze_position is not None:
            self.freeze_profit_offset += self.freeze_position.net_profit
            self.freeze_price_offset += (
                self.freeze_position.current_price - self.freeze_position.entry_price
            )
            result = self.bot.close_trade(
                self.bot,
                self.freeze_position,
                self.freeze_margin_after_open,
                min_open_duration,
                avg_open_duration_sum,
                open_duration_count,
                max_open_duration,
                is_utc,
            )
            self.freeze_position = None
        return result

    def do_exchange_and_freeze_close(
        self,
        min_open_duration,
        avg_open_duration_sum,
        open_duration_count,
        max_open_duration,
        is_utc=True,
    ):
        result = False
        if self.freeze_position is not None:
            self.freeze_price_offset += (
                self.freeze_position.current_price - self.freeze_position.entry_price
            )
            self.exchange()
            self.freeze_profit_offset += self.freeze_position.net_profit
            result = self.bot.close_trade(
                self.bot,
                self.freeze_position,
                self.freeze_margin_after_open,
                min_open_duration,
                avg_open_duration_sum,
                open_duration_count,
                max_open_duration,
                is_utc,
            )
            self.freeze_position = None
        return result

    def do_both_close(
        self,
        min_open_duration,
        avg_open_duration_sum,
        open_duration_count,
        max_open_duration,
        is_utc=True,
    ):
        if self.main_position is None and self.freeze_position is None:
            return False

        if self.main_position is not None:
            self.do_main_close(
                min_open_duration,
                avg_open_duration_sum,
                open_duration_count,
                max_open_duration,
                is_utc,
            )
            self.main_position = None

        if self.freeze_position is not None:
            self.do_freeze_close(
                min_open_duration,
                avg_open_duration_sum,
                open_duration_count,
                max_open_duration,
                is_utc,
            )
            self.freeze_position = None

        return True

    def close_frozen_and_modify_main(
        self,
        volume,
        min_open_duration,
        avg_open_duration_sum,
        open_duration_count,
        max_open_duration,
        is_utc=True,
    ):
        ret_val = False
        if self.main_position is None or self.freeze_position is None:
            return ret_val

        self.main_position.modify_volume(volume)
        ret_val = self.do_freeze_close(
            min_open_duration,
            avg_open_duration_sum,
            open_duration_count,
            max_open_duration,
            is_utc,
        )
        self.freeze_position = None

        return ret_val

    def close_main_and_modify_frozen(
        self,
        volume,
        min_open_duration,
        avg_open_duration_sum,
        open_duration_count,
        max_open_duration,
        is_utc=True,
    ):
        ret_val = False
        if self.main_position is None or self.freeze_position is None:
            return ret_val

        self.freeze_position.modify_volume(volume)
        ret_val = self.do_main_close(
            min_open_duration,
            avg_open_duration_sum,
            open_duration_count,
            max_open_duration,
            is_utc,
        )
        self.main_position = None

        return ret_val

    def reverse(
        self,
        volume,
        min_open_duration,
        avg_open_duration_sum,
        open_duration_count,
        max_open_duration,
        is_utc=True,
    ):
        ret_val = False
        if (
            self.main_position is None
            and self.freeze_position is None
            or self.main_position is not None
            and self.freeze_position is not None
        ):
            return ret_val

        if self.freeze_position is not None:
            self.do_freeze_close(
                min_open_duration,
                avg_open_duration_sum,
                open_duration_count,
                max_open_duration,
                is_utc,
            )
            self.freeze_position = None
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

    def exchange(self):
        if self.main_position is None or self.freeze_position is None:
            return False

        backup = self.main_position
        self.main_position = self.freeze_position
        self.freeze_position = backup

        return True

    def do_week_end_freeze(self, volume=0):
        if self.freeze_position is None:
            return self.do_freeze(self.weekend_freeze_id, volume)
        else:
            return False

    def do_freeze(self, labelExtension, volume):
        result = None
        if self.freeze_position is None:
            result = self.bot.open_trade(
                self.bot,
                self.symbol,
                TradeType.buy if not self.is_long else TradeType.sell,
                TradeDirection.long if not self.is_long else TradeDirection.short,
                "",
                self.label + labelExtension,
                self.symbol.normalize_volume_in_units(
                    self.main_position.initial_volume if volume == 0 else volume
                ),
            )

            if result is not None:
                self.freeze_position = result
                self.freeze_margin_after_open = self.bot.Account.margin
        return self.freeze_position is not None
