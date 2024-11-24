
class SystemSettings:
    def __init__(
        self,
        robot_name,
        default_symbol_name,  # for json must be exact same names as the member vars
        default_timeframe_value,
        default_timeframe_unit,
        TradeDirection,
        init_balance,
        start_dt,
        end_dt,
        is_visual_mode,
        speed,
        chart_bars,
        data_rate,
        Platform,
        platform_parameter,
    ):
        self.robot_name = robot_name
        self.default_symbol_name = default_symbol_name
        self.default_timeframe_value = default_timeframe_value
        self.default_timeframe_unit = default_timeframe_unit
        self.TradeDirection = TradeDirection
        self.init_balance = init_balance
        self.start_dt = start_dt
        self.end_dt = end_dt
        self.is_visual_mode = is_visual_mode
        self.speed = speed
        self.chart_bars = chart_bars
        self.data_rate = data_rate
        self.Platform = Platform
        self.platform_parameter = platform_parameter


class BinSettings:
    def __init__(
        self,
        robot_name,
        default_symbol_name,
        TradeDirection,
        init_balance,
        start_dt,
        end_dt,
        is_visual_mode,
        speed,
        bars_in_chart,
        default_timeframe_seconds,
        data_rate,
        Platform,
        platform_parameter,
    ):
        self.robot_name = robot_name
        self.default_symbol_name = default_symbol_name
        self.default_timeframe_seconds = default_timeframe_seconds
        self.TradeDirection = TradeDirection
        self.init_balance = init_balance
        self.start_dt = start_dt
        self.end_dt = end_dt
        self.is_visual_mode = is_visual_mode
        self.speed = speed
        self.bars_in_chart = bars_in_chart
        self.data_rate = data_rate
        self.Platform = Platform
        self.platform_parameter = platform_parameter


# end of file
