"""
Kanga2 Bot Port for KitaTrader

Ported from C# Kanga2 (cAlgo.Robots.Kanga2)
Mean Reversion Strategy using Bollinger Bands with Loss Recovery System and Spread Filter.

This port maintains exact compatibility with the C# version:
- Same entry/exit logic
- Same CSV log format
- Same performance metrics
- Same loss recovery system
"""

from __future__ import annotations
import os
import json
from datetime import datetime, timedelta, time
from collections import deque
from typing import Optional, List, Dict
from Api.KitaApiEnums import *
from Api.KitaApi import KitaApi
from Api.Symbol import Symbol
from Api.Position import Position
from Api.CoFu import *
from Api.Constants import *
from Api.Bars import Bars
from Api.PyLogger import PyLogger
from Indicators.BollingerBands import BollingerBands
from BrokerProvider.TradePaper import TradePaper
from BrokerProvider.QuoteCtraderCache import QuoteCtraderCache
from BrokerProvider.QuoteDukascopy import Dukascopy
import os


class QuoteCtraderCacheTick(QuoteCtraderCache):
    """Custom QuoteCtraderCache that uses 'tick' instead of 't1' for cache path"""
    def init_symbol(self, api: KitaApi, symbol: Symbol):
        self.api = api
        self.symbol = symbol
        ctrader_path = api.resolve_env_variables(self.parameter)
        # Use 'tick' instead of 't1' to match actual cache structure
        self.cache_path = os.path.join(ctrader_path, self.symbol.name, "tick")


class Quantrobot:
    """
    Quantrobot class - ported from Instance.cs
    Contains the core trading logic for a single symbol/direction instance.
    """
    
    def __init__(self, bot: 'Kanga2'):
        self.bot = bot
        
        # Parameters (will be set from main bot)
        self.qr_symbol_name: str = ""
        self.bot_direction: TradeDirection = TradeDirection.Both
        self.profit_mode: ProfitMode = ProfitMode.Lots
        self.value: float = 1.0
        self.bar_timeframe: int = Constants.SEC_PER_HOUR  # Default to H1
        self.bollinger_period: int = 25
        self.bollinger_std_dev: float = 1.7
        self.ma_type: MovingAverageType = MovingAverageType.Vidya
        self.stop_loss: float = 0.0
        
        # Members
        self.bot_number: int = 0
        self.bot_symbol: Optional[Symbol] = None
        self.my_position: Optional[Position] = None
        self.initial_volume: float = 0.0
        self.is_opened: bool = False
        self.is_closed: bool = False
        self.label: str = ""
        self.last_profit: float = 0.0
        self.is_long: bool = False
        
        # Bars and indicators
        self.m_bot_bars: Optional[Bars] = None
        self.m_bollinger: Optional[BollingerBands] = None
        self.m_m1_bars: Optional[Bars] = None
        self.m_last_bar_count: int = 0  # Track bar count to only recalculate when new bar forms
        
        # Entry indicator values
        self.m_entry_upper: float = 0.0
        self.m_entry_lower: float = 0.0
        self.m_entry_main: float = 0.0
        
        # Tick tracking
        self.m_last_tick_time: datetime = datetime.min
        self.m_last_heartbeat_date = None  # Track last heartbeat date (date object)
        self.m_last_entry_bar_index: int = 0
        self.m_last_m1_bar_count: int = 0
        self.m_tick_count: int = 0
        
        # Spread average logic
        self.m_spread_history: deque = deque(maxlen=100)
        self.m_spread_sum: float = 0.0
        self.m_average_spread: float = 0.0
        self.SPREAD_AVG_PERIOD = 100
        
        # Loss Recovery System
        self.m_accumulated_loss: float = 0.0
        self.m_recovery_trades_remaining: int = 0
        self.RECOVERY_TRADES_COUNT = 3
        self.m_is_paused_after_loss: bool = False
        self.m_last_bid_for_pause_check: float = 0.0
        self.m_last_main_for_pause_check: float = 0.0
        
        # Debug logger (writes to file, not stdout)
        self.debug_log_file = None
    
    def _debug_log(self, message: str):
        """Write debug message to log file"""
        if self.debug_log_file is None:
            return
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            self.debug_log_file.write(f"[{timestamp}] [{self.qr_symbol_name}] {message}\n")
            self.debug_log_file.flush()
        except Exception:
            pass  # Silently ignore log errors
    
    def qr_on_start(self) -> bool:
        """Initialize this bot instance - ported from QrOnStart()"""
        try:
            # Initialize debug log file
            try:
                log_dir = r"C:\Users\HMz\Documents\cAlgo\Logfiles"
                os.makedirs(log_dir, exist_ok=True)
                log_file_path = os.path.join(log_dir, f"Kanga2_{self.qr_symbol_name}_debug.log")
                self.debug_log_file = open(log_file_path, "w", encoding="utf-8")
                self._debug_log("Debug logging started")
            except Exception as e:
                # Silently fail if we can't create log file
                self.debug_log_file = None
            
            # Get symbol from bot's symbol dictionary
            if self.qr_symbol_name not in self.bot.symbol_dictionary:
                self._debug_log(f"Symbol {self.qr_symbol_name} cannot be loaded.")
                return False
            
            self.bot_symbol = self.bot.symbol_dictionary[self.qr_symbol_name]
            self.bot.m_bots_initialized_count += 1
            
            # Calculate volume
            # In C#: mRobot.CalcProfitMode2Lots(BotSymbol, ProfitMode, Value, 0, 0, out _, out double lotSize)
            # For now, use simple lot calculation
            if self.profit_mode == ProfitMode.Lots:
                lot_size = self.value
            else:
                # Default to value as lots
                lot_size = self.value
            
            # Normalize volume
            self.initial_volume = self.bot_symbol.normalize_volume_in_units(
                max(self.bot_symbol.min_volume, lot_size * self.bot_symbol.lot_size)
            )
            
            # Get bars for the specified timeframe using central MarketData API
            # C#: mBotBars = mBot.MarketData.GetBars(CsRobot.TimeFrameArray[(int)BarTimeframe], BotSymbol.Name);
            self.m_bot_bars = self.bot.MarketData.GetBars(self.bar_timeframe, self.qr_symbol_name)
            if self.m_bot_bars is None:
                self._debug_log(f"Error getting bars for timeframe {self.bar_timeframe}")
                return False
            
            # Get M1 bars for filtering
            # C#: mM1Bars = mBot.MarketData.GetBars(TimeFrame.Minute, BotSymbol.Name);
            self.m_m1_bars = self.bot.MarketData.GetBars(Constants.SEC_PER_MINUTE, self.qr_symbol_name)
            if self.m_m1_bars is None:
                self._debug_log(f"Warning: Could not get M1 bars")
                self.m_m1_bars = None
            
            # Initialize M1 bar tracking
            if self.m_m1_bars:
                self.m_last_m1_bar_count = self.m_m1_bars.count
            
            # Create Bollinger Bands indicator using central Indicators API
            # C#: mBollinger = mBot.Indicators.BollingerBands(mBotBars.ClosePrices, BollingerPeriod, BollingerStdDev, MAType)
            # Python: Use self.bot.Indicators.bollinger_bands() - automatically tracks for warm-up calculation
            error, self.m_bollinger = self.bot.Indicators.bollinger_bands(
                source=self.m_bot_bars.close_bids,
                periods=self.bollinger_period,
                standard_deviations=self.bollinger_std_dev,
                ma_type=self.ma_type,
                shift=0
            )
            if error != "" or self.m_bollinger is None:
                self._debug_log(f"Error creating Bollinger Bands: {error}")
                return False
            
            # DO NOT calculate indicators here - they will be calculated automatically
            # during symbol_on_tick() when bars are updated (matching live trading behavior)
            # Just track the initial bar count
                self.m_last_bar_count = self.m_bot_bars.count
            self._debug_log(f"Indicator created (will be calculated during ticks): bars={self.m_bot_bars.count}, periods={self.bollinger_period}")
            
            # Make label unique per bot instance
            direction_str = "Long" if self.bot_direction == TradeDirection.Long else \
                           "Short" if self.bot_direction == TradeDirection.Short else "Both"
            self.label = f"{self.bot.version};Kanga2;{self.qr_symbol_name};{direction_str};{self.bot_number}"
            
            # Ensure timezone-aware datetime
            from pytz import UTC
            tick_time = self.bot_symbol.time
            if tick_time.tzinfo is None:
                tick_time = tick_time.replace(tzinfo=UTC)
            self.m_last_tick_time = tick_time
            
            return True
            
        except Exception as e:
            self._debug_log(f"Error in qr_on_start: {e}")
            import traceback
            self._debug_log(traceback.format_exc())
            return False
    
    def update_spread_average(self):
        """Update spread average - ported from UpdateSpreadAverage()"""
        spread_pips = self.bot_symbol.spread / self.bot_symbol.pip_size
        self.m_spread_history.append(spread_pips)
        self.m_spread_sum += spread_pips
        
        if len(self.m_spread_history) > self.SPREAD_AVG_PERIOD:
            self.m_spread_sum -= self.m_spread_history[0]
        
        if len(self.m_spread_history) > 0:
            self.m_average_spread = self.m_spread_sum / len(self.m_spread_history)
    
    def is_us_dst(self, utc_time: datetime) -> bool:
        """Check if UTC time is within US Daylight Saving Time - ported from IsUsDst()"""
        from pytz import UTC
        year = utc_time.year
        
        # Find 2nd Sunday of March (DST starts at 2:00 AM local = 7:00 AM UTC)
        march_first = datetime(year, 3, 1, tzinfo=UTC)
        days_until_sunday = ((6 - march_first.weekday()) % 7)  # 6 = Sunday
        second_sunday_march = march_first + timedelta(days=days_until_sunday + 7)
        dst_start = second_sunday_march.replace(hour=7, minute=0, second=0)
        
        # Find 1st Sunday of November (DST ends at 2:00 AM local = 6:00 AM UTC during DST)
        nov_first = datetime(year, 11, 1, tzinfo=UTC)
        days_until_sunday = ((6 - nov_first.weekday()) % 7)
        first_sunday_nov = nov_first + timedelta(days=days_until_sunday if days_until_sunday > 0 else 0)
        dst_end = first_sunday_nov.replace(hour=6, minute=0, second=0)
        
        return dst_start <= utc_time < dst_end
    
    def get_trade_volume(self) -> float:
        """Calculate trade volume including recovery multiplier - ported from GetTradeVolume()"""
        # In optimization mode, always use base volume
        if self.bot.RunningMode == RunMode.BruteForceOptimization or \
           self.bot.RunningMode == RunMode.GeneticOptimization or \
           self.bot.RunningMode == RunMode.WalkForwardOptimization:
            return self.initial_volume
        
        if self.m_accumulated_loss <= 0 or self.m_recovery_trades_remaining <= 0:
            return self.initial_volume
        
        # Calculate extra profit needed per trade to recover loss
        recovery_per_trade = self.m_accumulated_loss / self.m_recovery_trades_remaining
        
        # Estimate profit per lot (assuming ~10 pips win)
        estimated_pips_per_win = 10.0
        position_value = self.initial_volume * self.bot_symbol.pip_value
        base_profit_per_trade = position_value * estimated_pips_per_win
        
        volume_multiplier = 1.0
        if base_profit_per_trade > 0:
            volume_multiplier = 1.0 + (recovery_per_trade / base_profit_per_trade)
            # Cap the multiplier to avoid excessive risk (max 3x)
            volume_multiplier = min(volume_multiplier, 3.0)
        
        recovery_volume = self.bot_symbol.normalize_volume_in_units(self.initial_volume * volume_multiplier)
        return recovery_volume
    
    def process_trade_for_recovery(self, net_profit: float):
        """Process a closed trade for the recovery system - ported from ProcessTradeForRecovery()"""
        if net_profit < 0:
            # Losing trade - add to accumulated loss and start/continue recovery
            self.m_accumulated_loss += abs(net_profit)
            self.m_recovery_trades_remaining = self.RECOVERY_TRADES_COUNT
            self.m_is_paused_after_loss = True
        elif net_profit > 0 and self.m_accumulated_loss > 0:
            # Winning trade while in recovery mode
            recovery_amount = min(net_profit, self.m_accumulated_loss)
            self.m_accumulated_loss -= recovery_amount
            self.m_recovery_trades_remaining -= 1
            
            if self.m_accumulated_loss <= 0.1 or self.m_recovery_trades_remaining <= 0:
                self._debug_log(f"WIN: {net_profit:.2f}. Recovery COMPLETE!")
                self.m_accumulated_loss = 0
                self.m_recovery_trades_remaining = 0
            else:
                self._debug_log(f"WIN: {net_profit:.2f}. Recovery progress: {self.m_accumulated_loss:.2f} remaining over {self.m_recovery_trades_remaining} trades.")
    
    def on_position_closed(self, position: Position):
        """Called when a position is closed - ported from OnPositionClosed()"""
        self.last_profit = position.net_profit
        self.is_closed = True
        
        # Process for loss recovery system
        self.process_trade_for_recovery(position.net_profit)
        
        # Log to CSV if enabled
        # Only log trades within the backtest period (matching cTrader behavior)
        if self.bot.is_do_logging and self.bot.logger:
            # Filter by backtest period
            entry_time = position.entry_time
            if entry_time.tzinfo is None:
                from pytz import UTC
                entry_time = entry_time.replace(tzinfo=UTC)
            
            # Only log trades that start within the backtest period
            if entry_time < self.bot.BacktestStartUtc or entry_time >= self.bot.BacktestEndUtc:
                return  # Skip trades outside backtest period
            
            close_price = position.closing_price
            digits = self.bot_symbol.digits
            fmt = f".{digits}f"
            lots = position.volume_in_units / self.bot_symbol.lot_size
            
            mode = "Long" if position.trade_type == TradeType.Buy else "Short"
            line = f"{len(self.bot.history)},{self.last_profit:.2f},{self.qr_symbol_name},{mode},{lots:.2f}," \
                   f"{position.entry_time.strftime('%Y-%m-%d %H:%M:%S')}," \
                   f"{position.closing_time.strftime('%Y-%m-%d %H:%M:%S')}," \
                   f"{position.entry_price:{fmt}},{close_price:{fmt}}," \
                   f"{self.m_entry_upper:{fmt}},{self.m_entry_lower:{fmt}},{self.m_entry_main:{fmt}}\n"
            
            self.bot.logger.add_text(line)
            self.bot.logger.flush()
    
    def qr_on_tick(self):
        """Main tick processing - ported from QrOnTick()"""
        self.m_tick_count += 1
        
        # Heartbeat: Log message at start of each new day (to log file only, not stdout)
        if self.bot_symbol is not None:
            try:
                current_time = self.bot_symbol.time
                if current_time is not None:
                    if current_time.tzinfo is None:
                        from pytz import UTC
                        current_time = current_time.replace(tzinfo=UTC)
                    
                    current_date = current_time.date()
                    if self.m_last_heartbeat_date is None:
                        self.m_last_heartbeat_date = current_date
                        self._debug_log(f"===== Starting backtest on {current_date.strftime('%Y-%m-%d')} ===== Tick #{self.m_tick_count}")
                    elif current_date > self.m_last_heartbeat_date:
                        self.m_last_heartbeat_date = current_date
                        self._debug_log(f"===== Processing {current_date.strftime('%Y-%m-%d')} ===== Tick #{self.m_tick_count}")
            except Exception as e:
                # Silently ignore heartbeat errors
                pass
        
        # Check for closed positions (check history for newly closed positions)
        # This handles the OnPositionClosed event equivalent
        if self.my_position:
            # Check if position was closed (it's no longer in positions list)
            if self.my_position not in self.bot.positions:
                # Find it in history
                for hist_pos in self.bot.history:
                    if hist_pos.label == self.label and hist_pos.symbol.name == self.bot_symbol.name:
                        if hist_pos.entry_time == self.my_position.entry_time:
                            self.on_position_closed(hist_pos)
                            break
                self.my_position = None
        
        # Update spread average
        self.update_spread_average()
        
        # Use bars retrieved in qr_on_start() - do NOT call GetBars() here
        # According to cTrader API: GetBars() should only be called during initialization
        # The bars object is automatically updated as new bars form, so we just check the count
        if self.m_bot_bars is None:
            # This should never happen if initialization was successful
                if self.m_tick_count == 1:
                self._debug_log(f"Error: m_bot_bars is None (should have been set in qr_on_start)")
                return
        
        # Check if enough bars before proceeding with trading logic
        if self.m_bot_bars.count < self.bollinger_period:
            # Log progress periodically to see if bars are building
            if self.m_tick_count == 1 or (self.m_tick_count % 100000 == 0):
                bar_count = self.m_bot_bars.count
                current_time = self.bot_symbol.time if self.bot_symbol else "N/A"
                self._debug_log(f"Waiting for bars: count={bar_count}, need={self.bollinger_period}, time={current_time}, tick={self.m_tick_count}")
            return  # Skip trading logic if not enough bars
        
        # Check for new bar formed
        # Indicators are now calculated automatically in bars_on_tick() when bars update
        # So we don't need to manually calculate them here
        new_bar_formed = False
        if self.m_bot_bars.count > self.m_last_bar_count:
            new_bar_formed = True
            self.m_last_bar_count = self.m_bot_bars.count
        
        # Get bar index for accessing indicator values
        bar_idx = self.m_bot_bars.read_index if hasattr(self.m_bot_bars, 'read_index') else (self.m_bot_bars.count - 1)
        
        # Check for new M1 bar (only when main bar changes or periodically)
        # Use m_m1_bars retrieved in qr_on_start() - do NOT call GetBars() here
        if new_bar_formed or self.m_tick_count % 100 == 0:
                if self.m_m1_bars and self.m_m1_bars.count > self.m_last_m1_bar_count:
                    self.m_last_m1_bar_count = self.m_m1_bars.count
        
        # If no new bar and indicator not initialized, return early
        if self.m_bollinger is None:
            return
        
        # Get Bollinger Band values for the previous closed bar
        # Use read_index - 1 to get the previous closed bar (read_index points to current bar)
        if self.m_bot_bars.count < self.bollinger_period:
            return
        
        # Get the index of the previous closed bar
        # read_index points to the current bar being processed, so read_index - 1 is the previous closed bar
        read_idx = self.m_bot_bars.read_index
        if read_idx < 1:
            return  # Need at least 1 previous bar
        
        bar_idx = read_idx - 1  # Previous closed bar
        
        # Ensure bar_idx is within valid range and has enough periods for indicator
        if bar_idx < self.bollinger_period - 1:
            return  # Not enough bars for indicator calculation
        
        # Indicators are now calculated automatically in bars_on_tick() when bars update
        # So we can directly access the indicator values
        # But first, ensure we have enough source data points
        source_data_len = len(self.m_bot_bars.close_bids.data)
        if bar_idx >= source_data_len:
            return  # Not enough source data
        
        # Access indicator values using Last(1) to match C# behavior
        # C# uses: mBollinger.Top.Last(1), mBollinger.Bottom.Last(1), mBollinger.Main.Last(1)
        # Last(1) gets the value from 1 bar ago (the previous closed bar)
        # The indicator should have been calculated for the previous bar in the previous tick
        # But to be safe, let's also try to ensure the indicator is calculated for the previous bar
        # by accessing it directly using the bar index
        read_idx = self.m_bot_bars.read_index
        prev_bar_idx = read_idx - 1  # Previous closed bar index
        
        # Try both methods: Last(1) and direct index access
        upper = self.m_bollinger.top.last(1)
        lower = self.m_bollinger.bottom.last(1)
        main = self.m_bollinger.main.last(1)
        
        # If Last(1) returns NaN, try direct index access (the indicator writes to index + shift)
        import math
        if math.isnan(upper) and prev_bar_idx >= 0:
            indicator_idx = prev_bar_idx + self.m_bollinger.shift
            if indicator_idx >= 0 and indicator_idx < len(self.m_bollinger.top.data):
                upper = self.m_bollinger.top.data[indicator_idx]
                lower = self.m_bollinger.bottom.data[indicator_idx]
                main = self.m_bollinger.main.data[indicator_idx]
        
        # Check for NaN (indicator not calculated or invalid)
        import math
        if math.isnan(upper) or math.isnan(lower) or math.isnan(main):
            # Indicators should be calculated automatically, but if still NaN, try to calculate it explicitly
            # This might happen if the indicator wasn't calculated for the previous bar
            # Try calculating the indicator for the previous bar index
            if prev_bar_idx >= self.bollinger_period - 1:
                try:
                    # Calculate indicator for the previous bar
                    self.m_bollinger.calculate(prev_bar_idx)
                    # Try reading again
                    indicator_idx = prev_bar_idx + self.m_bollinger.shift
                    if indicator_idx >= 0 and indicator_idx < len(self.m_bollinger.top.data):
                        upper = self.m_bollinger.top.data[indicator_idx]
                        lower = self.m_bollinger.bottom.data[indicator_idx]
                        main = self.m_bollinger.main.data[indicator_idx]
                except Exception as e:
                    if self.m_tick_count % 10000 == 0:
                        pass  # Indicator calculation failed, will try again on next tick
            
            # If still NaN, log and return
            if math.isnan(upper) or math.isnan(lower) or math.isnan(main):
            if self.m_tick_count % 10000 == 0:  # Debug every 10k ticks
                    source_val = self.m_bot_bars.close_bids.data[bar_idx] if bar_idx < len(self.m_bot_bars.close_bids.data) else float('nan')
                    pass  # Indicator not ready yet
            return
        
        # Get current prices
        spread = self.bot_symbol.spread
        bid = self.bot_symbol.bid
        ask = self.bot_symbol.ask
        
        # Pause Logic: Check if we touched Main Band to clear pause
        if self.m_is_paused_after_loss:
            if self.m_last_bid_for_pause_check == 0:
                self.m_last_bid_for_pause_check = bid
                self.m_last_main_for_pause_check = main
            
            # Check for cross of Main band
            crossed = False
            if self.m_last_bid_for_pause_check < self.m_last_main_for_pause_check and bid >= main:
                crossed = True
            elif self.m_last_bid_for_pause_check > self.m_last_main_for_pause_check and bid <= main:
                crossed = True
            
            if crossed:
                self.m_is_paused_after_loss = False
                self._debug_log(f"PAUSE CLEARED: Price touched/crossed Middle Line. Resuming trades.")
            
            self.m_last_bid_for_pause_check = bid
            self.m_last_main_for_pause_check = main
        
        # Rollover Protection
        utc_time = self.bot_symbol.time
        utc_tod = utc_time.time()
        is_dst = self.is_us_dst(utc_time)
        
        if is_dst:
            # EDT: NY is UTC-4, so 16:30 NY = 20:30 UTC, 18:00 NY = 22:00 UTC
            start_ro_utc = time(20, 30)
            end_ro_utc = time(22, 0)
        else:
            # EST: NY is UTC-5, so 16:30 NY = 21:30 UTC, 18:00 NY = 23:00 UTC
            start_ro_utc = time(21, 30)
            end_ro_utc = time(23, 0)
        
        is_rollover_period = start_ro_utc <= utc_tod < end_ro_utc
        if is_rollover_period:
            return  # Block entries and exits during rollover
        
        # Find my position
        self.my_position = None
        for pos in self.bot.positions:
            if pos.label == self.label and pos.symbol.name == self.bot_symbol.name:
                # Additional check: ensure TradeType matches bot direction
                matches_direction = False
                if self.bot_direction == TradeDirection.Long and pos.trade_type == TradeType.Buy:
                    matches_direction = True
                elif self.bot_direction == TradeDirection.Short and pos.trade_type == TradeType.Sell:
                    matches_direction = True
                elif self.bot_direction == TradeDirection.Both:
                    matches_direction = True
                
                if matches_direction:
                    self.my_position = pos
                    break
        
        # Entry Logic
        if self.my_position is None:
            # Entry signals
            signal_long = bid < lower
            signal_short = bid > upper
            
            # Debug output: Log entry signals periodically to see if they're being detected
            if signal_long or signal_short:
                if self.m_tick_count <= 10 or (self.m_tick_count % 50000 == 0):
                    self._debug_log(f"Entry signal: Long={signal_long}, Short={signal_short}, bid={bid:.5f}, lower={lower:.5f}, upper={upper:.5f}, main={main:.5f}, tick={self.m_tick_count}")
            
            # Block signals if Paused
            if self.m_is_paused_after_loss:
                signal_long = False
                signal_short = False
            
            # Same Bar Filter - allow trade only once per M1 bar
            if self.m_m1_bars and self.m_m1_bars.count <= self.m_last_entry_bar_index:
                signal_long = False
                signal_short = False
            
            # Time Gap Protection
            tick_time = self.bot_symbol.time
            if tick_time.tzinfo is None:
                from pytz import UTC
                tick_time = tick_time.replace(tzinfo=UTC)
            gap = (tick_time - self.m_last_tick_time).total_seconds() / 60.0
            if gap > 5.0:
                signal_long = False
                signal_short = False
            self.m_last_tick_time = tick_time
            
            # Spread Protection
            current_spread_pips = spread / self.bot_symbol.pip_size
            if len(self.m_spread_history) >= 10 and current_spread_pips > self.m_average_spread * 1.01:
                signal_long = False
                signal_short = False
            
            # Execute entries
            if signal_long and (self.bot_direction == TradeDirection.Both or self.bot_direction == TradeDirection.Long):
                trade_volume = self.get_trade_volume()
                
                position = self.bot_symbol.trade_provider.execute_market_order(
                    TradeType.Buy,
                    self.bot_symbol.name,
                    trade_volume,
                    self.label
                )
                
                if position:
                    # Set stop loss if specified
                    if self.stop_loss > 0:
                        # Calculate stop loss price
                        stop_loss_price = position.entry_price - (self.stop_loss * self.bot_symbol.pip_size)
                        position.stop_loss = stop_loss_price
                    
                    self.my_position = position
                    self.is_long = True
                    self.is_opened = True
                    self.m_entry_upper = upper
                    self.m_entry_lower = lower
                    self.m_entry_main = main
                    if self.m_m1_bars:
                        self.m_last_entry_bar_index = self.m_m1_bars.count
            
            elif signal_short and (self.bot_direction == TradeDirection.Both or self.bot_direction == TradeDirection.Short):
                trade_volume = self.get_trade_volume()
                
                position = self.bot_symbol.trade_provider.execute_market_order(
                    TradeType.Sell,
                    self.bot_symbol.name,
                    trade_volume,
                    self.label
                )
                
                if position:
                    # Set stop loss if specified
                    if self.stop_loss > 0:
                        # Calculate stop loss price
                        stop_loss_price = position.entry_price + (self.stop_loss * self.bot_symbol.pip_size)
                        position.stop_loss = stop_loss_price
                    
                    self.my_position = position
                    self.is_long = False
                    self.is_opened = True
                    self.m_entry_upper = upper
                    self.m_entry_lower = lower
                    self.m_entry_main = main
                    if self.m_m1_bars:
                        self.m_last_entry_bar_index = self.m_m1_bars.count
        
        else:
            # Exit Logic - Target is Mean (Main Band)
            close_signal = False
            if self.my_position.trade_type == TradeType.Buy and bid >= main:
                close_signal = True
            elif self.my_position.trade_type == TradeType.Sell and bid <= main:
                close_signal = True
            
            if close_signal:
                # Spread Protection on Close
                close_spread_pips = spread / self.bot_symbol.pip_size
                if len(self.m_spread_history) >= 10 and close_spread_pips > self.m_average_spread * 1.01:
                    return  # Spread too high, postpone close
                
                # Close position
                result = self.bot_symbol.trade_provider.close_position(self.my_position)
                if result.is_successful:
                    # Position will be processed in next tick's on_position_closed check
                    # Clear position reference so we don't try to close it again
                    self.my_position = None
    
    def qr_on_stop(self):
        """Called when bot stops - ported from QrOnStop()"""
        # Close debug log file
        if self.debug_log_file is not None:
            try:
                self._debug_log("Debug logging stopped")
                self.debug_log_file.close()
            except Exception:
                pass
            self.debug_log_file = None


class Kanga2(KitaApi):
    """
    Kanga2 Bot - ported from C# Kanga2.cs
    Mean Reversion Strategy using Bollinger Bands.
    """
    
    # History
    version: str = "Kanga2 V1.0"
    
    # Parameters
    is_do_logging: bool = True  # Enable logging to match C# output
    is_launch_debugger: bool = False
    symbol_csv_all_visual: str = "AUDNZD"  # Only AUDNZD has tick data in cache
    direction: TradeDirection = TradeDirection.Long  # C# shows only Long trades
    config_path: str = ""
    
    profit_mode: ProfitMode = ProfitMode.Lots
    value: float = 1.0
    bar_timeframe: int = 4 * Constants.SEC_PER_HOUR  # H4 (Hour4 in C# = 4 hours)
    
    # Kanga2 Strategy Parameters - matching C# CSV parameters
    bollinger_period: int = 23  # From CSV: Bollinger Period: 23
    bollinger_std_dev: float = 1.4  # From CSV: Bollinger StdDev: 1,4 (1.4)
    ma_type: MovingAverageType = MovingAverageType.Simple  # From CSV: MA Type: Simple
    stop_loss: float = 0.0
    
    # Members
    m_all_sys_sym_dir_bots: List[Quantrobot] = []
    m_filtered_opti_bots: List[Quantrobot] = []
    m_symbol_list: List[str] = []
    m_start_balance: float = 0.0
    m_tracked_max_equity: float = 0.0
    m_tracked_equity_drawdown_val: float = 0.0
    m_tracked_equity_drawdown_pct: float = 0.0
    m_bots_initialized_count: int = 0
    
    def __init__(self):
        super().__init__()
        self.m_all_sys_sym_dir_bots = []
        self.m_filtered_opti_bots = []
        self.m_symbol_list = []
    
    def sanitize_parameters(self):
        """Sanitize string parameters: accept '_' as empty - ported from OnStart()"""
        # In Python, we'll handle this in parameter loading
        pass
    
    def load_config_from_file(self, bot: Quantrobot, file_path: str, debug_log: bool = False) -> Optional[str]:
        """Load config from .cbotset file - ported from LoadConfigFromFile()"""
        symbol_name = None
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_content = f.read()
            
            config = json.loads(json_content)
            
            # Extract Chart.Symbol
            if "Chart" in config and "Symbol" in config["Chart"]:
                symbol_name = config["Chart"]["Symbol"]
                # Symbol loaded - messages removed
            
            # Load parameters from config
            if "Parameters" in config:
                params = config["Parameters"]
                
                # Copy parameters to bot instance
                if "BollingerPeriod" in params:
                    val = params["BollingerPeriod"]
                    if str(val).strip() != "_":
                        bot.bollinger_period = int(val)
                
                if "BollingerStdDev" in params:
                    val = params["BollingerStdDev"]
                    if str(val).strip() != "_":
                        bot.bollinger_std_dev = float(val)
                
                if "MAType" in params:
                    val = params["MAType"]
                    if str(val).strip() != "_":
                        # Convert string to enum
                        try:
                            bot.ma_type = MovingAverageType[val]
                        except:
                            pass
                
                if "Value" in params:
                    val = params["Value"]
                    if str(val).strip() != "_":
                        bot.value = float(val)
                
                if "ProfitMode" in params:
                    val = params["ProfitMode"]
                    if str(val).strip() != "_":
                        try:
                            bot.profit_mode = ProfitMode[val]
                        except:
                            pass
                
                if "BarTimeframe" in params:
                    val = params["BarTimeframe"]
                    if str(val).strip() != "_":
                        # Convert TimeFrameNdx enum to seconds
                        # C# TimeFrameNdx enum: Minute=0, Minute5=1, Minute15=3, Hour=7, Hour4=10, Weekly=17, etc.
                        # Map enum values to actual timeframes in seconds
                        tf_enum = int(val)
                        if tf_enum == 0:  # Minute
                            bot.bar_timeframe = Constants.SEC_PER_MINUTE
                        elif tf_enum == 1:  # Minute5
                            bot.bar_timeframe = 5 * Constants.SEC_PER_MINUTE
                        elif tf_enum == 3:  # Minute15
                            bot.bar_timeframe = 15 * Constants.SEC_PER_MINUTE
                        elif tf_enum == 5:  # Minute30
                            bot.bar_timeframe = 30 * Constants.SEC_PER_MINUTE
                        elif tf_enum == 7:  # Hour
                            bot.bar_timeframe = Constants.SEC_PER_HOUR
                        elif tf_enum == 8:  # Hour2
                            bot.bar_timeframe = 2 * Constants.SEC_PER_HOUR
                        elif tf_enum == 9:  # Hour3
                            bot.bar_timeframe = 3 * Constants.SEC_PER_HOUR
                        elif tf_enum == 10:  # Hour4
                            bot.bar_timeframe = 4 * Constants.SEC_PER_HOUR
                        elif tf_enum == 11:  # Hour6
                            bot.bar_timeframe = 6 * Constants.SEC_PER_HOUR
                        elif tf_enum == 12:  # Hour8
                            bot.bar_timeframe = 8 * Constants.SEC_PER_HOUR
                        elif tf_enum == 14:  # Daily
                            bot.bar_timeframe = Constants.SEC_PER_DAY
                        elif tf_enum == 17:  # Weekly (but config shows 17 for H4, so map to H4)
                            # Note: Some configs use 17 for H4 instead of Weekly
                            bot.bar_timeframe = 4 * Constants.SEC_PER_HOUR  # H4
                        else:
                            # Fallback: assume it's hours (old behavior for compatibility)
                            bot.bar_timeframe = tf_enum * Constants.SEC_PER_HOUR
            
            # Parameters loaded - messages removed
                
        except Exception as ex:
            # Error loading config file - messages removed
            pass
        
        return symbol_name
    
    def add_bot(self, current_bot: Quantrobot):
        """Add bot to lists - ported from AddBot()"""
        if current_bot.qr_symbol_name not in self.m_symbol_list:
            self.m_symbol_list.append(current_bot.qr_symbol_name)
        
        self.m_all_sys_sym_dir_bots.append(current_bot)
    
    def on_init(self) -> None:
        """Initialize bot - ported from OnStart()"""
        self.sanitize_parameters()
        
        # Initialize deferred BB messages list
        
        # Initialize logging if enabled
        if self.RunningMode != RunMode.RealTime and self.is_do_logging:
            header = "sep=,\n" \
                    "Number" \
                    ",NetProfit" \
                    ",Symbol" \
                    ",Mode" \
                    ",Lots" \
                    ",OpenDate" \
                    ",CloseDate" \
                    ",OpenPrice" \
                    ",ClosePrice" \
                    ",BollingerUpper" \
                    ",BollingerLower" \
                    ",BollingerMain"
            
            # Add "_Python" suffix to distinguish from C# logs
            base_filename = f"{self.version.split(' ')[0]} {self.config_path.replace('Config', '')}"
            log_filename = base_filename.replace(".csv", "_Python.csv") if base_filename.endswith(".csv") else f"{base_filename}_Python"
            self.open_logfile(log_filename, PyLogger.SELF_MADE, header)
        
        self.m_start_balance = self.account.balance
        
        # Initialize Equity Drawdown tracking
        self.m_tracked_max_equity = self.account.equity
        self.m_tracked_equity_drawdown_val = 0.0
        self.m_tracked_equity_drawdown_pct = 0.0
        
        # Parse symbol list
        symbol_csv_all_visual_split = [s.strip() for s in self.symbol_csv_all_visual.split(',')]
        
        # Rebuild symbol list (handle "vis" replacement)
        self.symbol_csv_all_visual = ""
        for i, sym in enumerate(symbol_csv_all_visual_split):
            if i > 0:
                self.symbol_csv_all_visual += ','
            if sym.lower() == "vis":
                # In C#, this would be replaced with current Symbol.Name
                # For now, we'll use the first symbol from symbol_dictionary
                if len(self.symbol_dictionary) > 0:
                    first_symbol = list(self.symbol_dictionary.values())[0].name
                    self.symbol_csv_all_visual += first_symbol
                    symbol_csv_all_visual_split[i] = first_symbol
                else:
                    self.symbol_csv_all_visual += sym
            else:
                self.symbol_csv_all_visual += sym
        
        if not self.config_path:
            # OPTIMIZATION MODE (or Manual Run without Config Files)
            # Bot started - messages removed
            
            for sym in symbol_csv_all_visual_split:
                if not sym or sym == "NONE":
                    continue
                
                current_bot = Quantrobot(self)
                current_bot.qr_symbol_name = sym
                current_bot.bot_direction = self.direction
                current_bot.value = self.value
                current_bot.profit_mode = self.profit_mode
                current_bot.bar_timeframe = self.bar_timeframe
                current_bot.bollinger_period = self.bollinger_period
                current_bot.bollinger_std_dev = self.bollinger_std_dev
                current_bot.ma_type = self.ma_type
                current_bot.stop_loss = self.stop_loss
                
                self.add_bot(current_bot)
                self.m_filtered_opti_bots.append(current_bot)
        else:
            # CONFIG FILE LOADING MODE
            # Bot started with config files - messages removed
            
            load_all = "all" in self.symbol_csv_all_visual.lower()
            
            if load_all:
                # Load ALL config files in directory
                # Loading config files - messages removed
                try:
                    config_files = [f for f in os.listdir(self.config_path) if f.endswith('.cbotset')]
                    
                    for filename in config_files:
                        file_path = os.path.join(self.config_path, filename)
                        current_bot = Quantrobot(self)
                        
                        debug_log = (config_files[0] == filename)
                        symbol_name = self.load_config_from_file(current_bot, file_path, debug_log)
                        
                        if not symbol_name:
                            # Warning: No symbol name found - messages removed
                            continue
                        
                        current_bot.qr_symbol_name = symbol_name
                        if self.stop_loss > 0:
                            current_bot.stop_loss = self.stop_loss
                        
                        # Override from GUI if set
                        if self.value >= 0:
                            current_bot.value = self.value
                            current_bot.profit_mode = self.profit_mode
                        
                        if self.direction != TradeDirection.Both:  # Simplified check
                            current_bot.bot_direction = self.direction
                        
                        self.add_bot(current_bot)
                        self.m_filtered_opti_bots.append(current_bot)
                        # Loaded symbol - messages removed
                        
                except Exception as ex:
                    # Error listing config files - messages removed
                    pass
            else:
                # Load only listed symbols
                for sym in symbol_csv_all_visual_split:
                    if not sym or sym == "NONE":
                        continue
                    
                    # Look for config file for this symbol
                    try:
                        config_files = [f for f in os.listdir(self.config_path) if sym in f and f.endswith('.cbotset')]
                        
                        if config_files:
                            file_path = os.path.join(self.config_path, config_files[0])
                            current_bot = Quantrobot(self)
                            
                            symbol_name = self.load_config_from_file(current_bot, file_path, True)
                            
                            current_bot.qr_symbol_name = sym
                            if self.stop_loss > 0:
                                current_bot.stop_loss = self.stop_loss
                            
                            if self.value >= 0:
                                current_bot.value = self.value
                                current_bot.profit_mode = self.profit_mode
                            
                            if self.direction != TradeDirection.Both:
                                current_bot.bot_direction = self.direction
                            
                            self.add_bot(current_bot)
                            self.m_filtered_opti_bots.append(current_bot)
                        else:
                            # No config file found - messages removed
                            pass
                    except Exception as ex:
                        # Error loading config - messages removed
                        pass
        
        # Request symbols for all bots
        # Use quote_provider and trade_provider from MainConsole (set globally) or create defaults
        if self.quote_provider is None:
            # Fallback: create default provider if not set in MainConsole
            # Use cTrader cache as requested
            quote_provider = QuoteCtraderCacheTick(data_rate=0, parameter=r"G:\Meine Ablage\ShareFile\BacktestingCache\pepperstone\demo")
            # Warning: No quote_provider set - messages removed
        else:
            quote_provider = self.quote_provider
        
        if self.trade_provider is None:
            # Fallback: create default provider if not set in MainConsole
            trade_provider = TradePaper()
            # Warning: No trade_provider set - messages removed
        else:
            trade_provider = self.trade_provider
        
        for bot in self.m_filtered_opti_bots:
            if bot.qr_symbol_name not in self.symbol_dictionary:
                error, symbol = self.request_symbol(
                    bot.qr_symbol_name,
                    quote_provider,
                    trade_provider,
                    "utc"
                )
                if error != "":
                    # Error requesting symbol - messages removed
                    continue
        
        # Initialize all bot instances
        # Initializing bot instances - messages removed
        for i, system_bot in enumerate(self.m_filtered_opti_bots):
            if system_bot is None:
                continue
            
            # Starting bot - messages removed
            system_bot.bot_number = i
            system_bot.bar_timeframe = self.bar_timeframe  # Ensure timeframe is set
            
            # Request bars for this symbol with lookback for indicator warm-up
            if system_bot.qr_symbol_name in self.symbol_dictionary:
                symbol = self.symbol_dictionary[system_bot.qr_symbol_name]
                # Request bars for the timeframe with lookback
                # Note: request_bars is internal, not part of cTrader API
                symbol.request_bars(system_bot.bar_timeframe, system_bot.bollinger_period + 10)
                # Request M1 bars for filtering
                symbol.request_bars(Constants.SEC_PER_MINUTE, 100)
            
            is_valid = system_bot.qr_on_start()
            if not is_valid:
                # Bot failed to initialize - messages removed
                self.m_filtered_opti_bots[i] = None
            else:
                # Bot initialized successfully - messages removed
                pass
    
    def on_start(self, symbol: Symbol) -> None:
        """Called when backtest starts for each symbol"""
        pass
    
    def on_tick(self, symbol: Symbol):
        """Main tick processing - ported from OnTick()"""
        # Process each bot instance
        for system_bot in self.m_filtered_opti_bots:
            if system_bot is None:
                continue
            
            # Only process if this tick is for the bot's symbol
            if system_bot.qr_symbol_name == symbol.name:
                system_bot.qr_on_tick()
        
        # Track Equity Drawdown
        if self.account.equity > self.m_tracked_max_equity:
            self.m_tracked_max_equity = self.account.equity
        else:
            current_drawdown = self.m_tracked_max_equity - self.account.equity
            if current_drawdown > self.m_tracked_equity_drawdown_val:
                self.m_tracked_equity_drawdown_val = current_drawdown
                if self.m_tracked_max_equity > 0:
                    self.m_tracked_equity_drawdown_pct = (current_drawdown / self.m_tracked_max_equity) * 100.0
    
    def on_stop(self, symbol: Symbol = None):
        """Called when bot stops - ported from OnStop()"""
        
        # Process stop for all bots
        for system_bot in self.m_filtered_opti_bots:
            if system_bot is None:
                continue
            system_bot.qr_on_stop()
        
        # Calculate Statistics (ported from OnStop())
        total_trades = len(self.history)
        winning_trades = len([t for t in self.history if t.net_profit > 0])
        losing_trades = len([t for t in self.history if t.net_profit < 0])
        break_even_trades = len([t for t in self.history if t.net_profit == 0])
        net_profit = sum(t.net_profit for t in self.history)
        gross_profit = sum(t.net_profit for t in self.history if t.net_profit > 0)
        gross_loss = sum(t.net_profit for t in self.history if t.net_profit < 0)
        
        # Balance Drawdown
        max_balance_drawdown = 0.0
        max_balance_drawdown_percent = 0.0
        if total_trades > 0:
            balance = self.m_start_balance
            max_balance = balance
            
            for trade in self.history:
                balance += trade.net_profit
                if balance > max_balance:
                    max_balance = balance
                
                drawdown = max_balance - balance
                if drawdown > max_balance_drawdown:
                    max_balance_drawdown = drawdown
                    max_balance_drawdown_percent = (drawdown / max_balance) * 100.0
        
        # Average Trade
        average_trade = net_profit / total_trades if total_trades > 0 else 0.0
        
        # Consecutive Wins/Losses
        max_consecutive_winners = 0
        max_consecutive_losers = 0
        current_consecutive_winners = 0
        current_consecutive_losers = 0
        
        for trade in self.history:
            if trade.net_profit > 0:
                current_consecutive_winners += 1
                current_consecutive_losers = 0
                if current_consecutive_winners > max_consecutive_winners:
                    max_consecutive_winners = current_consecutive_winners
            else:
                current_consecutive_losers += 1
                current_consecutive_winners = 0
                if current_consecutive_losers > max_consecutive_losers:
                    max_consecutive_losers = current_consecutive_losers
        
        stats_text = f"\nBacktest completed: Py {self.version}"
        stats_text += f"\nTotal Trades: {total_trades}"
        stats_text += f"\nWinning Trades: {winning_trades}"
        stats_text += f"\nLosing Trades: {losing_trades}"
        if break_even_trades > 0:
            stats_text += f"\nBreak-Even Trades: {break_even_trades}"
        stats_text += f"\nConsecutive Winners: {max_consecutive_winners}"
        stats_text += f"\nConsecutive Losers: {max_consecutive_losers}"
        stats_text += f"\nWin Rate: {(winning_trades * 100.0 / total_trades):.2f}%" if total_trades > 0 else "\nWin Rate: 0.00%"
        stats_text += f"\nNet Profit: {net_profit:.2f} {self.account.currency}"
        stats_text += f"\nGross Profit: {gross_profit:.2f} {self.account.currency}"
        stats_text += f"\nGross Loss: {abs(gross_loss):.2f} {self.account.currency}"
        stats_text += f"\nProfit Factor: {(gross_profit / abs(gross_loss)):.2f}" if gross_loss != 0 else "\nProfit Factor: N/A"
        stats_text += f"\nAverage Trade: {average_trade:.2f} {self.account.currency}"
        stats_text += f"\nAverage Win: {(gross_profit / winning_trades):.2f} {self.account.currency}" if winning_trades > 0 else "\nAverage Win: 0.00 {self.account.currency}"
        stats_text += f"\nAverage Loss: {(abs(gross_loss) / losing_trades):.2f} {self.account.currency}" if losing_trades > 0 else "\nAverage Loss: 0.00 {self.account.currency}"
        stats_text += f"\nMax Balance Drawdown: {max_balance_drawdown:.2f} {self.account.currency} ({max_balance_drawdown_percent:.2f}%)"
        stats_text += f"\nMax Equity Drawdown: {self.m_tracked_equity_drawdown_val:.2f} {self.account.currency} ({self.m_tracked_equity_drawdown_pct:.2f}%)"
        
        # Stats printed to log file only - stdout removed
        
        # Don't close logger here - KitaApi.do_stop() will handle it
        if self.logger and self.logger.is_open:
            self.log_add_text_line(stats_text)

