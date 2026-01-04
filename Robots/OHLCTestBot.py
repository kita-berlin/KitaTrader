"""
OHLC Test Bot - Compare tick values between C# and Python implementations
Logs all bars and indicators only on BarOpened events (1:1 lock step port from C# bot)
"""
import os
from datetime import datetime, timedelta
from Api.KitaApi import KitaApi
from Api.Symbol import Symbol
from Api.KitaApiEnums import *
from Api.Constants import Constants
from Api.BarOpenedEventArgs import BarOpenedEventArgs


class OHLCTestBot(KitaApi):
    """Test bot to log all OHLC values for comparison with C#"""
    
    def __init__(self):
        super().__init__()
        self.symbol_name = "AUDNZD"
        self.log_file = None
        self.debug_log_file = None
        self.bb_log_file = None
        self.sma_log_file = None
        # Bars for different timeframes
        self.m_bars_m1 = None  # M1 bars (60 seconds)
        self.m_bars_h1 = None  # H1 bars (3600 seconds)
        self.m_bars_h4 = None  # H4 bars (14400 seconds)
        # Track last logged counts for each timeframe
        self.last_logged_count_m1 = 0
        self.last_logged_count_h1 = 0
        self.last_logged_count_h4 = 0
        # Track last logged bar times for each timeframe (for ring buffer full detection)
        self._last_logged_bar_time_m1 = None
        self._last_logged_bar_time_h1 = None
        self._last_logged_bar_time_h4 = None
        # Bollinger Bands indicators on all OHLC values (for H4 only, as before)
        self.bb_open = None
        self.bb_high = None
        self.bb_low = None
        self.bb_close = None
        # Simple Moving Average indicators on all OHLC values for M1, H1, and H4
        # M1 SMAs
        self.sma_m1_open = None
        self.sma_m1_high = None
        self.sma_m1_low = None
        self.sma_m1_close = None
        # H1 SMAs
        self.sma_h1_open = None
        self.sma_h1_high = None
        self.sma_h1_low = None
        self.sma_h1_close = None
        # H4 SMAs (keep old names for backward compatibility)
        self.sma_open = None
        self.sma_high = None
        self.sma_low = None
        self.sma_close = None
        # BB parameters (matching Kanga2)
        self.bb_periods = 23
        self.bb_std_dev = 1.4
        # SMA parameters
        self.sma_periods = 23  # Same as BB for comparison
        
    def _debug_log(self, message: str):
        """Log debug messages to file"""
        if self.debug_log_file:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            self.debug_log_file.write(f"[{timestamp}] {message}\n")
            self.debug_log_file.flush()
    
    def on_init(self):
        """Initialize the bot and request H4 bars (matching Kanga2 timeframe)"""
        # Setup logging
        log_dir = r"C:\Users\HMz\Documents\cAlgo\Logfiles"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # TICK LOGGING DISABLED - Only OHLCV bar data is logged
        # log_path_ticks = os.path.join(log_dir, "OHLC_Test_Python_Ticks.csv")
        # self.log_file_ticks = open(log_path_ticks, "w", encoding="utf-8")
        # self.log_file_ticks.write("Time,Bid,Ask,Spread\n")
        # self.log_file_ticks.flush()
        self.log_file_ticks = None
        
        # Keep old log_file for backward compatibility
        self.log_file = None  # No tick logging
        
        # Bar tests - commented out for now, will test later
        log_path_m1 = os.path.join(log_dir, "OHLC_Test_Python_M1.csv")
        log_path_h1 = os.path.join(log_dir, "OHLC_Test_Python_H1.csv")
        log_path_h4 = os.path.join(log_dir, "OHLC_Test_Python_H4.csv")
        
        self.log_file_m1 = open(log_path_m1, "w", encoding="utf-8")
        m1_header = "Time,Open,High,Low,Close,Volume,SMAOpen,SMAHigh,SMALow,SMAClose\n"
        h1_header = "Time,Open,High,Low,Close,Volume,SMAOpen,SMAHigh,SMALow,SMAClose\n"
        h4_header = "Time,Open,High,Low,Close,Volume,SMAOpen,SMAHigh,SMALow,SMAClose\n"
        self.log_file_m1.write(m1_header)
        self.log_file_m1.flush()
        
        self.log_file_h1 = open(log_path_h1, "w", encoding="utf-8")
        self.log_file_h1.write(h1_header)
        self.log_file_h1.flush()
        
        self.log_file_h4 = open(log_path_h4, "w", encoding="utf-8")
        self.log_file_h4.write(h4_header)
        self.log_file_h4.flush()
        
        # Setup debug logging
        debug_log_path = os.path.join(log_dir, "OHLC_Test_Python_Debug.log")
        self.debug_log_file = open(debug_log_path, "w", encoding="utf-8")
        self._debug_log("OHLCTestBot: on_init() called")
        
        # Setup BB logging (for H4 indicators)
        bb_log_path = os.path.join(log_dir, "BB_Test_Python.log")
        self.bb_log_file = open(bb_log_path, "w", encoding="utf-8")
        self.bb_log_file.write("Time,Source,Main,Top,Bottom\n")
        self.bb_log_file.flush()
        
        # Setup SMA logging (with bar OHLC and bid/ask for verification)
        sma_log_path = os.path.join(log_dir, "SMA_Test_Python.log")
        self.sma_log_file = open(sma_log_path, "w", encoding="utf-8")
        self.sma_log_file.write("Time,Source,Value,BarOpen,BarHigh,BarLow,BarClose,BarOpenBid,BarOpenAsk\n")
        self.sma_log_file.flush()
        
        # Request symbol for tick testing only
        err, self.active_symbol = self.request_symbol(
            self.symbol_name, 
            self.quote_provider, 
            self.trade_provider
        )
        if err == "":
            # OHLCV bar testing only - no tick logging
            self._debug_log(f"OHLCTestBot: Initialized for OHLCV bar testing for {self.symbol_name}")
        else:
            self._debug_log(f"OHLCTestBot: Error requesting symbol: {err}")
        
        # Bar tests - commented out for now, will test later
        if err == "":
            self._debug_log(f"OHLCTestBot: Initialized for bar testing for {self.symbol_name}")
            # Request M1 bars (60 seconds)
            self.active_symbol.request_bars(60, 5000)  # 5000 bars for M1
            # Request H1 bars (3600 seconds = 1 hour)
            self.active_symbol.request_bars(3600, 200)  # 200 bars for H1
            # Request H4 bars (14400 seconds = 4 hours)
            self.active_symbol.request_bars(14400, 50)  # 50 bars for H4
            self._debug_log(f"OHLCTestBot: Requested M1, H1, and H4 bars for {self.symbol_name}")
            
            # Create indicators in on_init() - warmup phase ensures enough bars are available
            # Indicators must be created during initialization, not in on_start() or on_tick()
            self.m_bars_m1 = self.MarketData.GetBars(60, self.symbol_name)
            self.m_bars_h1 = self.MarketData.GetBars(3600, self.symbol_name)
            self.m_bars_h4 = self.MarketData.GetBars(14400, self.symbol_name)
            
            if self.m_bars_m1:
                self._create_sma_indicators(self.m_bars_m1, "M1",
                                           "sma_m1_open", "sma_m1_high", "sma_m1_low", "sma_m1_close")
            if self.m_bars_h1:
                self._create_sma_indicators(self.m_bars_h1, "H1",
                                           "sma_h1_open", "sma_h1_high", "sma_h1_low", "sma_h1_close")
            if self.m_bars_h4:
                self._create_sma_indicators(self.m_bars_h4, "H4",
                                           "sma_open", "sma_high", "sma_low", "sma_close")

    def on_start(self, symbol: Symbol) -> None:
        """Called when backtest starts for a specific symbol - OHLCV bar testing only"""
        # OHLCV bar testing only - no tick logging
        self._debug_log(f"OHLCTestBot: Started OHLCV bar testing for {self.symbol_name}")
        
        # Get M1, H1, and H4 Bars using MarketData API (already created in on_init, just get references)
        self.m_bars_m1 = self.MarketData.GetBars(60, self.symbol_name)  # M1 = 60 seconds
        self.m_bars_h1 = self.MarketData.GetBars(3600, self.symbol_name)  # H1 = 3600 seconds
        self.m_bars_h4 = self.MarketData.GetBars(14400, self.symbol_name)  # H4 = 14400 seconds
        
        if self.m_bars_m1 is None:
            self._debug_log(f"OHLCTestBot: Error getting M1 bars for {self.symbol_name}")
        else:
            self._debug_log(f"OHLCTestBot: Got M1 bars, initial count: {self.m_bars_m1.count}")
            self.last_logged_count_m1 = 0
            # Subscribe to BarOpened event for M1
            self.m_bars_m1.BarOpened += self.Bars_M1_BarOpened
            # Indicators are already created in on_init() - warmup ensures enough bars
        
        if self.m_bars_h1 is None:
            self._debug_log(f"OHLCTestBot: Error getting H1 bars for {self.symbol_name}")
        else:
            self._debug_log(f"OHLCTestBot: Got H1 bars, initial count: {self.m_bars_h1.count}")
            self.last_logged_count_h1 = 0
            # Subscribe to BarOpened event for H1
            self.m_bars_h1.BarOpened += self.Bars_H1_BarOpened
            # Indicators are already created in on_init() - warmup ensures enough bars
        
        if self.m_bars_h4 is None:
            self._debug_log(f"OHLCTestBot: Error getting H4 bars for {self.symbol_name}")
        else:
            self._debug_log(f"OHLCTestBot: Got H4 bars, initial count: {self.m_bars_h4.count}")
            self.last_logged_count_h4 = 0
            self._bb_indicators_created = False  # Track if BB indicators have been created
            # Subscribe to BarOpened event for H4
            self.m_bars_h4.BarOpened += self.Bars_H4_BarOpened
            # Indicators are already created in on_init() - warmup ensures enough bars
        
        # Keep old m_bars for backward compatibility (H4)
        self.m_bars = self.m_bars_h4
        self.last_logged_count = self.last_logged_count_h4
    
    def _create_sma_indicators(self, bars, timeframe_name: str, 
                               attr_open: str, attr_high: str, attr_low: str, attr_close: str):
        """Create SMA indicators for a given timeframe"""
        if bars is None:
            return
        
        self._debug_log(f"Creating Simple Moving Average on all OHLC values for {timeframe_name} (periods={self.sma_periods})")
        
        # SMA on Open (using correct property name matching H4 method)
        error, sma_open = self.Indicators.moving_average(
            source=bars.OpenPrices,
            periods=self.sma_periods,
            ma_type=MovingAverageType.Simple
        )
        if error == "":
            setattr(self, attr_open, sma_open)
        else:
            self._debug_log(f"Error creating SMA on Open for {timeframe_name}: {error}")
        
        # SMA on High
        error, sma_high = self.Indicators.moving_average(
            source=bars.HighPrices,
            periods=self.sma_periods,
            ma_type=MovingAverageType.Simple
        )
        if error == "":
            setattr(self, attr_high, sma_high)
        else:
            self._debug_log(f"Error creating SMA on High for {timeframe_name}: {error}")
        
        # SMA on Low
        error, sma_low = self.Indicators.moving_average(
            source=bars.LowPrices,
            periods=self.sma_periods,
            ma_type=MovingAverageType.Simple
        )
        if error == "":
            setattr(self, attr_low, sma_low)
        else:
            self._debug_log(f"Error creating SMA on Low for {timeframe_name}: {error}")
        
        # SMA on Close
        error, sma_close = self.Indicators.moving_average(
            source=bars.ClosePrices,
            periods=self.sma_periods,
            ma_type=MovingAverageType.Simple
        )
        if error == "":
            setattr(self, attr_close, sma_close)
        else:
            self._debug_log(f"Error creating SMA on Close for {timeframe_name}: {error}")
        
        if getattr(self, attr_open, None) and getattr(self, attr_high, None) and \
           getattr(self, attr_low, None) and getattr(self, attr_close, None):
            self._debug_log(f"Simple Moving Average created successfully on all OHLC values for {timeframe_name}")

    def _log_bars_for_timeframe(self, bars, timeframe_name: str, log_file, last_logged_count_attr: str, last_logged_time_attr: str, symbol: Symbol,
                                 sma_open=None, sma_high=None, sma_low=None, sma_close=None):
        """Helper method to log bars for a specific timeframe"""
        if bars is None or bars.count == 0:
            return
        
        # Get the last logged count and time for this timeframe
        last_logged_count = getattr(self, last_logged_count_attr, 0)
        last_logged_bar_time = getattr(self, last_logged_time_attr, None)
        
        # Update last_logged_count to current count on first call (after warm-up, bars may have been created)
        if last_logged_count == 0:
            last_logged_count = bars.count
            setattr(self, last_logged_count_attr, last_logged_count)
        
        # Check for new bars: check if bar time changed (works even when ring buffer is full)
        new_bar_detected = False
        if bars.count > 1:  # Need at least 2 bars (current + previous)
            prevBar = bars.Last(1)  # Previous closed bar
            if prevBar:
                barTime = prevBar.OpenTime
                
                # Check if this is a new bar we haven't logged yet
                if bars.count > last_logged_count:
                    # Count increased - definitely a new bar
                    new_bar_detected = True
                elif last_logged_bar_time is not None and barTime != last_logged_bar_time:
                    # Ring buffer is full (count == size), but bar time changed - new bar overwrote oldest
                    new_bar_detected = True
                    self._debug_log(f"[on_tick] {timeframe_name} new bar detected via time change: barTime={barTime}, _last_logged_bar_time={last_logged_bar_time}, count={bars.count}")
                elif last_logged_bar_time is None:
                    # First time logging - always log
                    new_bar_detected = True
                
                if new_bar_detected:
                    # Debug logging for bar filtering
                    self._debug_log(f"[on_tick] {timeframe_name} new bar detected: count={bars.count}, last_logged={last_logged_count}, barTime={barTime}, BacktestStartUtc={self.BacktestStartUtc}, BacktestEndUtc={self.BacktestEndUtc}")
        
        if new_bar_detected and bars.count > 1:
            # When a new bar forms, log the previous closed bar (Last(1))
            prevBar = bars.Last(1)
            barTime = prevBar.OpenTime
            
            # Only log bars within backtest period
            if barTime < self.BacktestStartUtc:
                self._debug_log(f"[on_tick] {timeframe_name} bar filtered: barTime ({barTime}) < BacktestStartUtc ({self.BacktestStartUtc})")
                setattr(self, last_logged_count_attr, bars.count)
                setattr(self, last_logged_time_attr, barTime)
                return
            if barTime >= self.BacktestEndUtc:
                self._debug_log(f"[on_tick] {timeframe_name} bar filtered: barTime ({barTime}) >= BacktestEndUtc ({self.BacktestEndUtc})")
                setattr(self, last_logged_count_attr, bars.count)
                setattr(self, last_logged_time_attr, barTime)
                return
            
            # Bar is within date range - log it
            self._debug_log(f"[on_tick] {timeframe_name} bar passed filter, logging: barTime={barTime}, count={bars.count}")
            barOpen = prevBar.Open
            barHigh = prevBar.High
            barLow = prevBar.Low
            barClose = prevBar.Close
            digits = symbol.digits
            fmt = f".{digits}f"
            
            # Get bar index for the previous bar (the one that just closed)
            barIndex = bars.count - 2
            
            # Get SMA values if indicators are available
            smaOpenVal = ""
            smaHighVal = ""
            smaLowVal = ""
            smaCloseVal = ""
            
            if sma_open and sma_high and sma_low and sma_close:
                import math
                # Calculate SMA values for the previous bar (barIndex)
                # Matching H4 method: calculate indicator for barIndex, then use last(0) to get result
                # barIndex = bars.count - 2 (for Last(1) bar)
                if barIndex >= 0 and barIndex >= self.sma_periods - 1:
                    try:
                        # Calculate indicators for this bar index (matching H4 method pattern)
                        # Ensure we calculate for the correct index (barIndex = bars.count - 2 for Last(1) bar)
                        sma_open.calculate(barIndex)
                        sma_high.calculate(barIndex)
                        sma_low.calculate(barIndex)
                        sma_close.calculate(barIndex)
                        
                        # Access result using shifted index (matching C#: Result[index2] where index2 = index + Shift)
                        result_index = barIndex + sma_open.shift
                        smaOpenVal = sma_open.result[result_index]
                        smaHighVal = sma_high.result[result_index]
                        smaLowVal = sma_low.result[result_index]
                        smaCloseVal = sma_close.result[result_index]
                        
                        # Debug: Log if values are NaN
                        if math.isnan(smaOpenVal) or math.isnan(smaHighVal) or math.isnan(smaLowVal) or math.isnan(smaCloseVal):
                            self._debug_log(f"[on_tick] {timeframe_name} SMA values are NaN for barIndex={barIndex}: Open={smaOpenVal}, High={smaHighVal}, Low={smaLowVal}, Close={smaCloseVal}")
                        
                        # Check for NaN values and convert to empty string
                        if math.isnan(smaOpenVal):
                            smaOpenVal = ""
                        if math.isnan(smaHighVal):
                            smaHighVal = ""
                        if math.isnan(smaLowVal):
                            smaLowVal = ""
                        if math.isnan(smaCloseVal):
                            smaCloseVal = ""
                    except Exception as e:
                        self._debug_log(f"Error calculating SMA for {timeframe_name} barIndex {barIndex}: {e}")
                        import traceback
                        self._debug_log(f"Traceback: {traceback.format_exc()}")
            
            # Format SMA values
            if smaOpenVal != "":
                smaOpenVal = f"{smaOpenVal:{fmt}}"
            if smaHighVal != "":
                smaHighVal = f"{smaHighVal:{fmt}}"
            if smaLowVal != "":
                smaLowVal = f"{smaLowVal:{fmt}}"
            if smaCloseVal != "":
                smaCloseVal = f"{smaCloseVal:{fmt}}"
            
            # Log OHLC values with Volume and SMA (matching C# FINAL_BAR format: Time|Open|High|Low|Close|Volume|SMAOpen|SMAHigh|SMALow|SMAClose)
            time_str = barTime.strftime("%Y-%m-%d %H:%M:%S")
            barVolume = prevBar.TickVolume
            log_line = f"{time_str},{barOpen:{fmt}},{barHigh:{fmt}},{barLow:{fmt}},{barClose:{fmt}},{barVolume},{smaOpenVal},{smaHighVal},{smaLowVal},{smaCloseVal}\n"
            log_file.write(log_line)
            log_file.flush()

            
            # Update last_logged_count and last_logged_bar_time after successful logging
            setattr(self, last_logged_count_attr, bars.count)
            setattr(self, last_logged_time_attr, barTime)
    
    def on_tick(self, symbol: Symbol):
        """Main tick processing - TICK LOGGING DISABLED, only OHLCV bars are logged"""
        # TICK LOGGING DISABLED - Only OHLCV bar data is logged in BarOpened event handlers
        # if symbol.time is None:
        #     return
        # 
        # # Log tick: Time,Bid,Ask,Spread
        # time_str = symbol.time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Include milliseconds
        # digits = symbol.digits
        # fmt = f".{digits}f"
        # log_line = f"{time_str},{symbol.bid:{fmt}},{symbol.ask:{fmt}},{symbol.spread:{fmt}}\n"
        # self.log_file_ticks.write(log_line)
        # self.log_file_ticks.flush()
        
        # Indicators are created only in on_init() - warmup phase ensures enough bars are available
        # Bar and indicator logging now happens only in BarOpened event handlers
        # No bar logging in on_tick - only tick logging remains
    
    def Bars_M1_BarOpened(self, args: BarOpenedEventArgs):
        """BarOpened event handler for M1 bars - logs bars and indicators only on BarOpened"""
        bars = args.Bars
        symbol = self.active_symbol
        if bars is None or bars.count < 2 or symbol is None:
            return
        
        # Get the previous closed bar (Last(1))
        prevBar = bars.Last(1)
        if prevBar is None:
            return
        
        barTime = prevBar.OpenTime
        
        # Match C# bot behavior: only log bars within backtest period (start <= barTime < end)
        # C# bot checks: bar.OpenTime >= startDate && bar.OpenTime < endDate
        if barTime < self.BacktestStartUtc or barTime >= self.BacktestEndUtc:
            return
        
        # Log the closed bar with indicators
        self._log_bar_with_indicators(
            bars, prevBar, barTime, "M1", self.log_file_m1, symbol,
            self.sma_m1_open, self.sma_m1_high, self.sma_m1_low, self.sma_m1_close
        )
    
    def Bars_H1_BarOpened(self, args: BarOpenedEventArgs):
        """BarOpened event handler for H1 bars - logs bars and indicators only on BarOpened"""
        bars = args.Bars
        symbol = self.active_symbol
        if bars is None or bars.count < 2 or symbol is None:
            return
        
        # Get the previous closed bar (Last(1))
        prevBar = bars.Last(1)
        if prevBar is None:
            return
        
        barTime = prevBar.OpenTime
        
        # Match C# bot behavior: only log bars within backtest period (start <= barTime < end)
        # C# bot checks: bar.OpenTime >= startDate && bar.OpenTime < endDate
        if barTime < self.BacktestStartUtc or barTime >= self.BacktestEndUtc:
            return
        
        # Log the closed bar with indicators
        self._log_bar_with_indicators(
            bars, prevBar, barTime, "H1", self.log_file_h1, symbol,
            self.sma_h1_open, self.sma_h1_high, self.sma_h1_low, self.sma_h1_close
        )
    
    def Bars_H4_BarOpened(self, args: BarOpenedEventArgs):
        """BarOpened event handler for H4 bars - logs bars and indicators only on BarOpened"""
        bars = args.Bars
        symbol = self.active_symbol
        if bars is None or bars.count < 2 or symbol is None:
            return
        
        # Get the previous closed bar (Last(1))
        prevBar = bars.Last(1)
        if prevBar is None:
            return
        
        barTime = prevBar.OpenTime
        
        # Match C# bot behavior: only log bars within backtest period (start <= barTime < end)
        # C# bot checks: bar.OpenTime >= startDate && bar.OpenTime < endDate
        if barTime < self.BacktestStartUtc or barTime >= self.BacktestEndUtc:
            return
        
        # Create indicators if not created yet and enough bars are available
        if not self._bb_indicators_created and bars.count >= self.bb_periods:
            self._create_bb_indicators(bars)
        
        # Log the closed bar with indicators
        self._log_bar_with_indicators(
            bars, prevBar, barTime, "H4", self.log_file_h4, symbol,
            self.sma_open, self.sma_high, self.sma_low, self.sma_close
        )
        
        # Log indicator values for H4 (BB and SMA)
        self._log_h4_indicators(bars, prevBar, barTime, symbol)
    
    def _log_bar_with_indicators(self, bars, prevBar, barTime, timeframe_name: str, log_file, symbol: Symbol,
                                 sma_open=None, sma_high=None, sma_low=None, sma_close=None):
        """Helper method to log a bar with indicator values"""
        barOpen = prevBar.Open
        barHigh = prevBar.High
        barLow = prevBar.Low
        barClose = prevBar.Close
        digits = symbol.digits
        fmt = f".{digits}f"
        
        # Get bar index for the previous bar (the one that just closed)
        barIndex = bars.count - 2
        
        # Get SMA values if indicators are available
        smaOpenVal = ""
        smaHighVal = ""
        smaLowVal = ""
        smaCloseVal = ""
        
        if sma_open and sma_high and sma_low and sma_close:
            import math
            if barIndex >= 0 and barIndex >= self.sma_periods - 1:
                try:
                    # Calculate indicators for this bar index
                    sma_open.calculate(barIndex)
                    sma_high.calculate(barIndex)
                    sma_low.calculate(barIndex)
                    sma_close.calculate(barIndex)
                    
                    smaOpenVal = sma_open.result[barIndex]
                    smaHighVal = sma_high.result[barIndex]
                    smaLowVal = sma_low.result[barIndex]
                    smaCloseVal = sma_close.result[barIndex]
                    
                    # Check for NaN values and convert to empty string
                    if math.isnan(smaOpenVal):
                        smaOpenVal = ""
                    else:
                        smaOpenVal = f"{smaOpenVal:{fmt}}"
                    if math.isnan(smaHighVal):
                        smaHighVal = ""
                    else:
                        smaHighVal = f"{smaHighVal:{fmt}}"
                    if math.isnan(smaLowVal):
                        smaLowVal = ""
                    else:
                        smaLowVal = f"{smaLowVal:{fmt}}"
                    if math.isnan(smaCloseVal):
                        smaCloseVal = ""
                    else:
                        smaCloseVal = f"{smaCloseVal:{fmt}}"
                except Exception as e:
                    self._debug_log(f"Error calculating SMA for {timeframe_name} barIndex {barIndex}: {e}")
        
        # Log OHLC values with Volume and SMA (matching C# FINAL_BAR format: Time|Open|High|Low|Close|Volume|SMAOpen|SMAHigh|SMALow|SMAClose)
        time_str = barTime.strftime("%Y-%m-%d %H:%M:%S")
        barVolume = prevBar.TickVolume
        log_line = f"{time_str},{barOpen:{fmt}},{barHigh:{fmt}},{barLow:{fmt}},{barClose:{fmt}},{barVolume},{smaOpenVal},{smaHighVal},{smaLowVal},{smaCloseVal}\n"
        log_file.write(log_line)
        log_file.flush()
    
    def _create_bb_indicators(self, bars):
        """Create Bollinger Bands indicators for H4"""
        self._debug_log(f"Creating Bollinger Bands on all OHLC values (periods={self.bb_periods}, std_dev={self.bb_std_dev})")
        
        error, self.bb_open = self.Indicators.bollinger_bands(
            source=bars.OpenPrices,
            periods=self.bb_periods,
            standard_deviations=self.bb_std_dev,
            ma_type=MovingAverageType.Simple,
            shift=0
        )
        if error != "":
            self._debug_log(f"Error creating BB on Open: {error}")
        
        error, self.bb_high = self.Indicators.bollinger_bands(
            source=bars.HighPrices,
            periods=self.bb_periods,
            standard_deviations=self.bb_std_dev,
            ma_type=MovingAverageType.Simple,
            shift=0
        )
        if error != "":
            self._debug_log(f"Error creating BB on High: {error}")
        
        error, self.bb_low = self.Indicators.bollinger_bands(
            source=bars.LowPrices,
            periods=self.bb_periods,
            standard_deviations=self.bb_std_dev,
            ma_type=MovingAverageType.Simple,
            shift=0
        )
        if error != "":
            self._debug_log(f"Error creating BB on Low: {error}")
        
        error, self.bb_close = self.Indicators.bollinger_bands(
            source=bars.ClosePrices,
            periods=self.bb_periods,
            standard_deviations=self.bb_std_dev,
            ma_type=MovingAverageType.Simple,
            shift=0
        )
        if error != "":
            self._debug_log(f"Error creating BB on Close: {error}")
        
        if self.bb_open and self.bb_high and self.bb_low and self.bb_close:
            self._debug_log("Bollinger Bands created successfully on all OHLC values")
            self._bb_indicators_created = True
    
    def _log_h4_indicators(self, bars, prevBar, barTime, symbol: Symbol):
        """Log indicator values for H4 (BB and SMA)"""
        barIndex = bars.count - 2
        
        # Log Simple Moving Average values
        if barIndex >= self.sma_periods - 1 and self.sma_open and self.sma_high and self.sma_low and self.sma_close:
            import math
            try:
                # Ensure indicators are calculated for this bar index
                self.sma_open.calculate(barIndex)
                self.sma_high.calculate(barIndex)
                self.sma_low.calculate(barIndex)
                self.sma_close.calculate(barIndex)
                
                # Get bid and ask at bar open time for verification
                barOpenBid = bars.open_bids.last(1) if barIndex >= 0 else 0.0
                barOpenAsk = bars.open_asks.last(1) if barIndex >= 0 else 0.0
                
                digits = symbol.digits
                fmt = f".{digits}f"
                time_str = barTime.strftime("%Y-%m-%d %H:%M:%S")
                barOpen = prevBar.Open
                barHigh = prevBar.High
                barLow = prevBar.Low
                barClose = prevBar.Close
                
                smaOpen = self.sma_open.result[barIndex]
                if not math.isnan(smaOpen):
                    self.sma_log_file.write(f"{time_str},Open,{smaOpen:{fmt}},{barOpen:{fmt}},{barHigh:{fmt}},{barLow:{fmt}},{barClose:{fmt}},{barOpenBid:{fmt}},{barOpenAsk:{fmt}}\n")
                
                smaHigh = self.sma_high.result[barIndex]
                if not math.isnan(smaHigh):
                    self.sma_log_file.write(f"{time_str},High,{smaHigh:{fmt}},{barOpen:{fmt}},{barHigh:{fmt}},{barLow:{fmt}},{barClose:{fmt}},{barOpenBid:{fmt}},{barOpenAsk:{fmt}}\n")
                
                smaLow = self.sma_low.result[barIndex]
                if not math.isnan(smaLow):
                    self.sma_log_file.write(f"{time_str},Low,{smaLow:{fmt}},{barOpen:{fmt}},{barHigh:{fmt}},{barLow:{fmt}},{barClose:{fmt}},{barOpenBid:{fmt}},{barOpenAsk:{fmt}}\n")
                
                smaClose = self.sma_close.result[barIndex]
                if not math.isnan(smaClose):
                    self.sma_log_file.write(f"{time_str},Close,{smaClose:{fmt}},{barOpen:{fmt}},{barHigh:{fmt}},{barLow:{fmt}},{barClose:{fmt}},{barOpenBid:{fmt}},{barOpenAsk:{fmt}}\n")
                
                self.sma_log_file.flush()
            except (IndexError, AttributeError, TypeError) as e:
                self._debug_log(f"Error logging SMA values for barIndex {barIndex}: {e}")
        
        # Log Bollinger Bands values
        if barIndex >= self.bb_periods - 1 and self.bb_open and self.bb_high and self.bb_low and self.bb_close:
            import math
            try:
                # Ensure indicators are calculated for this bar index
                self.bb_open.calculate(barIndex)
                self.bb_high.calculate(barIndex)
                self.bb_low.calculate(barIndex)
                self.bb_close.calculate(barIndex)
                
                digits = symbol.digits
                fmt = f".{digits}f"
                time_str = barTime.strftime("%Y-%m-%d %H:%M:%S")
                
                bbOpenMain = self.bb_open.main[barIndex]
                bbOpenTop = self.bb_open.top[barIndex]
                bbOpenBottom = self.bb_open.bottom[barIndex]
                if not math.isnan(bbOpenMain):
                    self.bb_log_file.write(f"{time_str},Open,{bbOpenMain:{fmt}},{bbOpenTop:{fmt}},{bbOpenBottom:{fmt}}\n")
                
                bbHighMain = self.bb_high.main[barIndex]
                bbHighTop = self.bb_high.top[barIndex]
                bbHighBottom = self.bb_high.bottom[barIndex]
                if not math.isnan(bbHighMain):
                    self.bb_log_file.write(f"{time_str},High,{bbHighMain:{fmt}},{bbHighTop:{fmt}},{bbHighBottom:{fmt}}\n")
                
                bbLowMain = self.bb_low.main[barIndex]
                bbLowTop = self.bb_low.top[barIndex]
                bbLowBottom = self.bb_low.bottom[barIndex]
                if not math.isnan(bbLowMain):
                    self.bb_log_file.write(f"{time_str},Low,{bbLowMain:{fmt}},{bbLowTop:{fmt}},{bbLowBottom:{fmt}}\n")
                
                bbCloseMain = self.bb_close.main[barIndex]
                bbCloseTop = self.bb_close.top[barIndex]
                bbCloseBottom = self.bb_close.bottom[barIndex]
                if not math.isnan(bbCloseMain):
                    self.bb_log_file.write(f"{time_str},Close,{bbCloseMain:{fmt}},{bbCloseTop:{fmt}},{bbCloseBottom:{fmt}}\n")
                
                self.bb_log_file.flush()
            except (IndexError, AttributeError, TypeError) as e:
                self._debug_log(f"Error logging BB values for barIndex {barIndex}: {e}")
    
    def on_stop(self, symbol: Symbol = None):
        """Cleanup when backtest ends"""
        if self.log_file_ticks:
            self.log_file_ticks.close()
        if self.log_file:
            self.log_file.close()
        # Indicator tests - commented out for now
        if self.bb_log_file:
            self.bb_log_file.close()
        if self.sma_log_file:
            self.sma_log_file.close()
        if self.debug_log_file:
            self._debug_log("OHLC Test completed")
            self.debug_log_file.close()

