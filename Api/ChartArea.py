from enum import Enum
from abc import ABC


class ChartType(Enum):
    Bar = 1
    Candlesticks = 2
    Line = 3
    Dots = 4


class Timeframe(Enum):
    OneMinute = 1
    OneHour = 2
    OneDay = 3
    OneWeek = 4
    OneMonth = 5


class ChartArea(ABC):
    @property
    def is_alive(self) -> bool:
        pass

    @property
    def width(self) -> float:
        pass

    @property
    def height(self) -> float:
        pass

    @property
    def bottom_y(self) -> float:
        pass

    @property
    def top_y(self) -> float:
        pass


class chart_activation_changed_event_args:
    pass  # Define chart_activation_changed_event_args class according to your requirement


class chart_display_settings_event_args:
    pass  # Define chart_display_settings_event_args class according to your requirement


class chart_color_event_args:
    pass  # Define chart_color_event_args class according to your requirement


class chart_type_event_args:
    pass  # Define chart_type_event_args class according to your requirement


class chart_zoom_event_args:
    pass  # Define chart_zoom_event_args class according to your requirement


class indicator_area_added_event_args:
    pass  # Define indicator_area_added_event_args class according to your requirement


class indicator_area_removed_event_args:
    pass  # Define indicator_area_removed_event_args class according to your requirement


class chart_keyboard_event_args:
    pass  # Define chart_keyboard_event_args class according to your requirement


class chart_visibility_changed_event_args:
    pass  # Define chart_visibility_changed_event_args class according to your requirement
