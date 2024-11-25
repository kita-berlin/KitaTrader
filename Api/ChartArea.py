from typing import List, Union
from enum import Enum
from abc import ABC, abstractmethod
from datetime import datetime


class ChartType(Enum):
    bar = 1
    candlesticks = 2
    line = 3
    dots = 4


class Timeframe(Enum):
    one_minute = 1
    one_hour = 2
    one_day = 3
    one_week = 4
    one_month = 5


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
