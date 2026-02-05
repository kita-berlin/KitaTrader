from Api.IIndicator import IIndicator
from Api.DataSeries import DataSeries
from Indicators.StandardIndicator import StandardIndicator
from datetime import datetime
import math


class RelativeStrengthIndex(StandardIndicator, IIndicator):
    """
    Relative Strength Index (RSI) indicator.
    1:1 port from cTrader RelativeStrengthIndexIndicator.
    Uses EMAs with 2*Periods-1 periods for gains/losses, exactly like C# version.
    """
    def __init__(self, source: DataSeries, periods: int = 14):
        super().__init__(source, periods)
        
        # Internal DataSeries for gains and losses (like C# _gains and _losses)
        self._gains = None
        self._losses = None
        
        # Internal EMAs (like C# _exponentialMovingAverageGain and _exponentialMovingAverageLoss)
        self._exponentialMovingAverageGain = None
        self._exponentialMovingAverageLoss = None
        
        # Debug: Store last calculated EMA values for exact logging
        self._last_ema_gain = None
        self._last_ema_loss = None
        self._last_calc_index = -1
        self._last_gain = None
        self._last_loss = None

    def initialize(self) -> None:
        """
        1:1 port from C# RelativeStrengthIndexIndicator.Initialize()
        """
        from Api.DataSeries import DataSeries
        
        # Create internal DataSeries for gains and losses
        # These need to be DataSeries with the same parent as source
        self._gains = DataSeries(self.source._parent, 2000, is_indicator_result=False)
        self._losses = DataSeries(self.source._parent, 2000, is_indicator_result=False)
        
        # Create EMAs with 2*Periods-1 periods (exactly like C#)
        from Indicators.ExponentialMovingAverage import ExponentialMovingAverage
        from Api.KitaApiEnums import MovingAverageType
        
        ema_periods = 2 * self.periods - 1
        self._exponentialMovingAverageGain = ExponentialMovingAverage(self._gains, ema_periods)
        self._exponentialMovingAverageGain.initialize()
        
        self._exponentialMovingAverageLoss = ExponentialMovingAverage(self._losses, ema_periods)
        self._exponentialMovingAverageLoss.initialize()

    def calculate(self, index: int) -> None:
        """
        1:1 port from cTrader RelativeStrengthIndexIndicator.Calculate(int index)
        """
        if index < 1:
            # Need at least 2 source values to calculate gain/loss
            self.result[index] = float('nan')
            return
        
        # Calculate gains and losses (exactly like C#)
        num = self.source[index]
        num2 = self.source[index - 1]
        
        # DEBUG: Log for H4 timeframe when index <= 5
        if hasattr(self.source, '_parent') and hasattr(self.source._parent, 'timeframe_seconds'):
            tf_seconds = self.source._parent.timeframe_seconds
            if tf_seconds == 14400 and index <= 5:  # H4 timeframe
                if hasattr(self.source._parent, '_symbol') and hasattr(self.source._parent._symbol, 'api'):
                    robot = self.source._parent._symbol.api.robot
                    if hasattr(robot, '_debug_log'):
                        try:
                            if hasattr(self.source._parent, 'open_times') and self.source._parent.open_times._add_count > index:
                                bar_time = self.source._parent.open_times[index]
                                robot._debug_log(f"RSI H4 calculate(index={index}): num={num:.5f}, num2={num2:.5f}, bar_time={bar_time}")
                            else:
                                robot._debug_log(f"RSI H4 calculate(index={index}): num={num:.5f}, num2={num2:.5f}, no bar_time")
                        except Exception as e:
                            robot._debug_log(f"RSI H4 calculate(index={index}): num={num:.5f}, num2={num2:.5f}, exception={e}")
        
        # Debug: Log for H4 timeframe when index <= 10
        if hasattr(self.source, '_parent') and hasattr(self.source._parent, 'timeframe_seconds'):
            tf_seconds = self.source._parent.timeframe_seconds
            if tf_seconds == 14400 and index <= 10:  # H4 timeframe
                if hasattr(self.source._parent, '_symbol') and hasattr(self.source._parent._symbol, 'api'):
                    robot = self.source._parent._symbol.api.robot
                    if hasattr(robot, '_debug_log'):
                        try:
                            if hasattr(self.source._parent, 'open_times') and self.source._parent.open_times._add_count > index:
                                bar_time = self.source._parent.open_times[index]
                                robot._debug_log(f"RSI H4 calculate(index={index}): num={num:.5f}, num2={num2:.5f}, bar_time={bar_time}")
                            else:
                                robot._debug_log(f"RSI H4 calculate(index={index}): num={num:.5f}, num2={num2:.5f}, no bar_time")
                        except:
                            robot._debug_log(f"RSI H4 calculate(index={index}): num={num:.5f}, num2={num2:.5f}, exception")
        
        # CRITICAL: Match C# behavior for first bar after warmup
        # C# sets Source[0] = Source[1] if no previous bar exists (Gain/Loss = 0.0)
        # Python needs to do the same: for the first bar that can have gain/loss (index >= 1),
        # if source[index-1] is from warmup period, treat source[index-1] as equal to source[index] (Gain/Loss = 0.0)
        # This matches C# behavior where the first logged bar has Gain/Loss = 0.0
        is_first_bar_after_warmup = False
        try:
            if hasattr(self.source, '_parent') and hasattr(self.source._parent, '_symbol'):
                symbol = self.source._parent._symbol
                if hasattr(symbol, 'api') and hasattr(symbol.api, 'robot'):
                    robot = symbol.api.robot
                    if hasattr(robot, '_BacktestStartUtc') and robot._BacktestStartUtc != datetime.min:
                        # Check if source[index-1] (previous bar) is from warmup period
                        # If so, treat as C# does (Source[index-1] = Source[index], so Gain/Loss = 0.0)
                        if hasattr(self.source._parent, 'open_times'):
                            add_count = getattr(self.source._parent.open_times, '_add_count', 0)
                            if add_count > index and index >= 1:  # Need at least index-1 and index
                                bar_time_prev = self.source._parent.open_times[index - 1]
                                backtest_start = robot._BacktestStartUtc
                                # Compare times (handle both timezone-aware and naive)
                                if hasattr(bar_time_prev, 'tzinfo') and bar_time_prev.tzinfo is not None:
                                    # bar_time_prev is timezone-aware
                                    if hasattr(backtest_start, 'tzinfo') and backtest_start.tzinfo is not None:
                                        # Both timezone-aware, compare directly
                                        if bar_time_prev < backtest_start:
                                            is_first_bar_after_warmup = True
                                    else:
                                        # backtest_start is naive, assume UTC
                                        import pytz
                                        backtest_start_utc = pytz.UTC.localize(backtest_start) if backtest_start.tzinfo is None else backtest_start
                                        if bar_time_prev < backtest_start_utc:
                                            is_first_bar_after_warmup = True
                                else:
                                    # bar_time_prev is naive, compare directly (assuming both are in same timezone)
                                    if bar_time_prev < backtest_start:
                                        is_first_bar_after_warmup = True
        except:
            pass
        
        if is_first_bar_after_warmup:
            # C# behavior: Source[index-1] = Source[index], so Gain/Loss = 0.0
            gain_val = 0.0
            loss_val = 0.0
        else:
            # Normal calculation
            if num > num2:
                gain_val = num - num2
                loss_val = 0.0
            elif num < num2:
                gain_val = 0.0
                loss_val = num2 - num
            else:
                gain_val = 0.0
                loss_val = 0.0
        
        self._gains[index] = gain_val
        self._losses[index] = loss_val
        
        # Store exact gain/loss values for debugging (before any rounding/formatting)
        self._last_gain = gain_val
        self._last_loss = loss_val
        
        # Calculate EMAs for this index (they will handle their own lazy calculation)
        # The EMAs need to be calculated for every index, even if RSI result is NaN
        # Accessing result[index] will trigger lazy calculation automatically
        # EXACTLY like C#: no explicit NaN check, division will produce NaN if either is NaN
        ema_gain = self._exponentialMovingAverageGain.result[index]
        ema_loss = self._exponentialMovingAverageLoss.result[index]
        
        # Store exact EMA values for debugging (before any rounding/formatting)
        # These will be used by OHLCTestBot to log the exact values used in calculation
        self._last_ema_gain = ema_gain
        self._last_ema_loss = ema_loss
        self._last_calc_index = index
        
        # EXACTLY like C#: direct division without NaN check
        # In C#, if ema_loss is 0.0, num3 = ema_gain / 0.0 = Infinity (double.PositiveInfinity)
        # In Python, we need to handle this explicitly to match C# behavior
        if ema_loss == 0.0:
            # C#: num3 = Infinity, Result = 100.0 - 100.0 / (1.0 + Infinity) = 100.0 - 0.0 = 100.0
            # But actually, C# will produce Infinity, and 100.0 / (1.0 + Infinity) = 0.0, so Result = 100.0
            num3 = float('inf') if ema_gain > 0.0 else float('-inf') if ema_gain < 0.0 else float('nan')
        else:
            num3 = ema_gain / ema_loss
        
        # C#: Result[index] = 100.0 - 100.0 / (1.0 + num3)
        # If num3 is Infinity, then 1.0 + Infinity = Infinity, and 100.0 / Infinity = 0.0, so Result = 100.0
        # If num3 is NaN, then Result = NaN
        self.result[index] = 100.0 - 100.0 / (1.0 + num3)
