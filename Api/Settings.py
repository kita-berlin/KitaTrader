from datetime import datetime
from AlgoApiEnums import DataRates, TradeDirection, Platforms


class StrSettings:
    def __init__(
        self,
        robot_name: str,
        default_symbol_name: str,  # for json must be exact same names as the member vars
        default_timeframe_value: str,
        default_timeframe_unit: str,
        trade_direction: str,
        init_balance: str,
        start_dt: str,
        end_dt: str,
        is_visual_mode: str,
        speed: str,
        chart_bars: str,
        data_rate: str,
        platform: str,
        platform_parameter: str,
    ):
        self.robot_name: str = robot_name
        self.default_symbol_name: str = default_symbol_name
        self.default_timeframe_value: str = default_timeframe_value
        self.default_timeframe_unit: str = default_timeframe_unit
        self.trade_direction: str = trade_direction
        self.init_balance: str = init_balance
        self.start_dt: str = start_dt
        self.end_dt: str = end_dt
        self.is_visual_mode: str = is_visual_mode
        self.speed: str = speed
        self.chart_bars: str = chart_bars
        self.data_rate: str = data_rate
        self.platform: str = platform
        self.platform_parameter: str = platform_parameter


class BinSettings:
    def __init__(
        self,
        robot_name: str,
        default_symbol_name: str,
        trade_direction: TradeDirection,
        init_balance: float,
        start_dt: datetime,
        end_dt: datetime,
        is_visual_mode: bool,
        speed: int,
        bars_in_chart: int,
        default_timeframe_seconds: int,
        data_rate: DataRates,
        platform: Platforms,
        platform_parameter: str,
    ):
        self.robot_name: str = robot_name
        self.default_symbol_name: str = default_symbol_name
        self.default_timeframe_seconds: int = default_timeframe_seconds
        self.trade_direction: TradeDirection = trade_direction
        self.init_balance: float = init_balance
        self.start_dt: datetime = start_dt
        self.end_dt: datetime = end_dt
        self.is_visual_mode: bool = is_visual_mode
        self.speed: int = speed
        self.bars_in_chart: int = bars_in_chart
        self.data_rate: DataRates = data_rate
        self.platform: Platforms = platform
        self.platform_parameter: str = platform_parameter


# end of file
