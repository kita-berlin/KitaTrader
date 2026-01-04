"""
OHLC Test Bot - 1:1 lock step port from C# OHLCTestBot
Logs bars with SMA indicators - matches C# bot logic exactly
"""
import os
from datetime import datetime
from Api.KitaApi import KitaApi
from Api.Symbol import Symbol
from Api.BarOpenedEventArgs import BarOpenedEventArgs


class OHLCTestBot(KitaApi):
    """Test bot to log all OHLC values with SMA for comparison with C# - 1:1 port"""
    
    def __init__(self):
        super().__init__()
        self.symbol_name = "AUDNZD"
        
        # Bars for different timeframes (matching C#: mBarsM1, mBarsM5, mBarsH1, mBarsH4)
        self.m_bars_m1 = None  # M1 bars (1 minute)
        self.m_bars_m5 = None  # M5 bars (5 minutes)
        self.m_bars_h1 = None  # H1 bars (1 hour)
        self.m_bars_h4 = None  # H4 bars (4 hours)
        
        # Track last bar counts (matching C#: mLastBarCountM1, etc.)
        self.m_last_bar_count_m1 = 0
        self.m_last_bar_count_m5 = 0
        self.m_last_bar_count_h1 = 0
        self.m_last_bar_count_h4 = 0
        
        # Simple Moving Average indicators on all OHLC values for all timeframes
        # M1 SMAs
        self.m_sma_m1_open = None
        self.m_sma_m1_high = None
        self.m_sma_m1_low = None
        self.m_sma_m1_close = None
        # M5 SMAs
        self.m_sma_m5_open = None
        self.m_sma_m5_high = None
        self.m_sma_m5_low = None
        self.m_sma_m5_close = None
        # H1 SMAs
        self.m_sma_h1_open = None
        self.m_sma_h1_high = None
        self.m_sma_h1_low = None
        self.m_sma_h1_close = None
        # H4 SMAs
        self.m_sma_h4_open = None
        self.m_sma_h4_high = None
        self.m_sma_h4_low = None
        self.m_sma_h4_close = None
        
        # SMA parameters
        self.m_sma_periods = 23
        
        # Log file for output (matching C# Print() behavior)
        self.log_file = None
    
    def on_init(self) -> None:
        """
        Python framework requires on_init to request symbol and bars
        C# equivalent: OnInit doesn't exist, everything is in OnStart
        But Python requires: request_symbol in on_init, then GetBars in on_start
        """
        # Open log file (matching C# Print() output location)
        log_dir = r"C:\Users\HMz\Documents\cAlgo\Logfiles"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_path = os.path.join(log_dir, "OHLCTestBot_Python.log")
        self.log_file = open(log_path, "w", encoding="utf-8")
        
        # Request symbol (Python framework requirement)
        # C#: Symbol is available automatically via Robot.Symbol
        err, self.active_symbol = self.request_symbol(
            self.symbol_name,
            self.quote_provider,
            self.trade_provider
        )
        if err != "":
            self._log(f"Error requesting symbol: {err}")
            return
        
        # Request bars for all timeframes (Python framework requirement)
        # C#: Bars are requested via MarketData.GetBars() in OnStart
        # Python: Bars must be requested in on_init, then accessed in on_start
        if self.active_symbol:
            self.active_symbol.request_bars(60, 2000)      # M1: 2000 bars
            self.active_symbol.request_bars(300, 500)      # M5: 500 bars
            self.active_symbol.request_bars(3600, 100)     # H1: 100 bars
            self.active_symbol.request_bars(14400, 50)     # H4: 50 bars
    
    def on_start(self, symbol: Symbol) -> None:
        """
        1:1 port from C# OnStart()
        """
        # C#: Print($"OHLCTestBot started: Symbol={Symbol.Name} - Tick testing mode");
        self._log(f"OHLCTestBot started: Symbol={symbol.name} - Tick testing mode")
        
        # C#: Get bars for all timeframes: M1, M5, H1, H4
        # mBarsM1 = MarketData.GetBars(TimeFrame.Minute, Symbol.Name);
        # mBarsM5 = MarketData.GetBars(TimeFrame.Minute5, Symbol.Name);
        # mBarsH1 = MarketData.GetBars(TimeFrame.Hour, Symbol.Name);
        # mBarsH4 = MarketData.GetBars(TimeFrame.Hour4, Symbol.Name);
        self.m_bars_m1 = self.MarketData.GetBars(60, self.symbol_name)      # M1 = 60 seconds
        self.m_bars_m5 = self.MarketData.GetBars(300, self.symbol_name)     # M5 = 300 seconds
        self.m_bars_h1 = self.MarketData.GetBars(3600, self.symbol_name)    # H1 = 3600 seconds
        self.m_bars_h4 = self.MarketData.GetBars(14400, self.symbol_name)   # H4 = 14400 seconds
        
        # C#: Check if all bars are null
        if self.m_bars_m1 is None or self.m_bars_m5 is None or self.m_bars_h1 is None or self.m_bars_h4 is None:
            self._log(f"Error: Could not get all bars for {self.symbol_name}")
            if self.m_bars_m1 is None:
                self._log("  M1 bars: null")
            if self.m_bars_m5 is None:
                self._log("  M5 bars: null")
            if self.m_bars_h1 is None:
                self._log("  H1 bars: null")
            if self.m_bars_h4 is None:
                self._log("  H4 bars: null")
            self.Stop()
            return
        
        # C#: Print($"OHLCTestBot started: Symbol={Symbol.Name} - M1, M5, H1, H4 bars");
        self._log(f"OHLCTestBot started: Symbol={self.symbol_name} - M1, M5, H1, H4 bars")
        self._log(f"Initial M1 bar count: {self.m_bars_m1.count}")
        self._log(f"Initial M5 bar count: {self.m_bars_m5.count}")
        self._log(f"Initial H1 bar count: {self.m_bars_h1.count}")
        self._log(f"Initial H4 bar count: {self.m_bars_h4.count}")
        
        self.m_last_bar_count_m1 = 0
        self.m_last_bar_count_m5 = 0
        self.m_last_bar_count_h1 = 0
        self.m_last_bar_count_h4 = 0
        
        # Create SMA indicators for all timeframes - warmup phase ensures enough bars are available
        self.create_sma_indicators(self.m_bars_m1, "M1")
        self.create_sma_indicators(self.m_bars_m5, "M5")
        self.create_sma_indicators(self.m_bars_h1, "H1")
        self.create_sma_indicators(self.m_bars_h4, "H4")
        
        # Subscribe to BarOpened events for all timeframes
        self.m_bars_m1.BarOpened += lambda args: self.on_bar_opened("M1", args)
        self.m_bars_m5.BarOpened += lambda args: self.on_bar_opened("M5", args)
        self.m_bars_h1.BarOpened += lambda args: self.on_bar_opened("H1", args)
        self.m_bars_h4.BarOpened += lambda args: self.on_bar_opened("H4", args)
        self._log("Subscribed to M1, M5, H1, H4 BarOpened events.")
    
    def create_sma_indicators(self, bars, timeframe_name):
        """
        1:1 port from C# CreateSMAIndicators
        """
        if not bars or bars.count < self.m_sma_periods:
            return
            
        self._log(f"Creating Simple Moving Average on all OHLC values for {timeframe_name} (periods={self.m_sma_periods})")
        
        # SMA on Open
        sma_open = self.Indicators.simple_moving_average(bars.OpenPrices, self.m_sma_periods)
        
        # SMA on High
        sma_high = self.Indicators.simple_moving_average(bars.HighPrices, self.m_sma_periods)
        
        # SMA on Low
        sma_low = self.Indicators.simple_moving_average(bars.LowPrices, self.m_sma_periods)
        
        # SMA on Close
        sma_close = self.Indicators.simple_moving_average(bars.ClosePrices, self.m_sma_periods)
        
        # Store indicators by timeframe
        if timeframe_name == "M1":
            self.m_sma_m1_open = sma_open
            self.m_sma_m1_high = sma_high
            self.m_sma_m1_low = sma_low
            self.m_sma_m1_close = sma_close
        elif timeframe_name == "M5":
            self.m_sma_m5_open = sma_open
            self.m_sma_m5_high = sma_high
            self.m_sma_m5_low = sma_low
            self.m_sma_m5_close = sma_close
        elif timeframe_name == "H1":
            self.m_sma_h1_open = sma_open
            self.m_sma_h1_high = sma_high
            self.m_sma_h1_low = sma_low
            self.m_sma_h1_close = sma_close
        elif timeframe_name == "H4":
            self.m_sma_h4_open = sma_open
            self.m_sma_h4_high = sma_high
            self.m_sma_h4_low = sma_low
            self.m_sma_h4_close = sma_close
        
        self._log(f"Simple Moving Average created successfully on all OHLC values for {timeframe_name}")
    
    def on_tick(self, symbol: Symbol):
        """
        1:1 port from C# OnTick()
        C#: NO FILTERING - Log EVERY tick that cTrader sends to OnTick()
        """
        # C#: var timeStr = Time.ToString("yyyy-MM-dd HH:mm:ss.fff");
        time_str = symbol.time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] if symbol.time else ""
        
        # C#: var fmt = "F20";
        fmt = ".20f"
        
        # C#: var tickLine = $"{timeStr},{Symbol.Bid.ToString(tickFmt, CultureInfo.InvariantCulture)},{Symbol.Ask.ToString(tickFmt, CultureInfo.InvariantCulture)},{Symbol.Spread.ToString(tickFmt, CultureInfo.InvariantCulture)}";
        # C#: Print(tickLine);
        tick_line = f"{time_str},{symbol.bid:{fmt}},{symbol.ask:{fmt}},{symbol.spread:{fmt}}"
        self._log(tick_line)
    
    def on_stop(self, symbol: Symbol = None):
        """
        1:1 port from C# OnStop()
        C#: // Cleanup when backtest ends (no logging here)
        """
        if self.log_file:
            self.log_file.close()
            self.log_file = None
    
    def on_bar_opened(self, tf: str, args: BarOpenedEventArgs):
        """
        1:1 port from C# OnBarOpened(string tf, BarOpenedEventArgs args)
        C#: Log the CLOSED bar (Last(1))
        """
        # C#: if (args.Bars.Count < 2) return;
        if args.Bars.count < 2:
            return
        
        # C#: var bar = args.Bars.Last(1);
        bar = args.Bars.Last(1)
        if bar is None:
            return
        
        # C#: var index = args.Bars.Count - 2;
        # Python: Use absolute index counter from RingBuffer
        # args.Bars.count is capped at ring buffer size, but we need total added count
        index = args.Bars._bar_buffer._add_count - 2
        
        # C#: var fmt = "F20";
        fmt = ".20f"
        
        # Get SMAs for this timeframe
        sma_o, sma_h, sma_l, sma_c = None, None, None, None
        if tf == "M1":
             sma_o, sma_h, sma_l, sma_c = self.m_sma_m1_open, self.m_sma_m1_high, self.m_sma_m1_low, self.m_sma_m1_close
        elif tf == "M5":
             sma_o, sma_h, sma_l, sma_c = self.m_sma_m5_open, self.m_sma_m5_high, self.m_sma_m5_low, self.m_sma_m5_close
        elif tf == "H1":
             sma_o, sma_h, sma_l, sma_c = self.m_sma_h1_open, self.m_sma_h1_high, self.m_sma_h1_low, self.m_sma_h1_close
        elif tf == "H4":
             sma_o, sma_h, sma_l, sma_c = self.m_sma_h4_open, self.m_sma_h4_high, self.m_sma_h4_low, self.m_sma_h4_close
        
        sO = ""
        sH = ""
        sL = ""
        sC = ""
        
        import math
        # Helper to get result safely
        def get_sma_val(sma, idx):
            if sma and idx >= 0:
                 # result uses ringbuffer, so use idx which is absolute
                 # DataSeries handles abs index
                 try:
                    val = sma.result[idx]
                    if not math.isnan(val):
                        return f"{val:{fmt}}"
                 except:
                    pass
            return ""

        if index >= self.m_sma_periods - 1:
             sO = get_sma_val(sma_o, index)
             sH = get_sma_val(sma_h, index)
             sL = get_sma_val(sma_l, index)
             sC = get_sma_val(sma_c, index)
        
        # C#: // Date range filtering is handled "under the hood" by the platform/API
        # C#: // Log all bars that reach this point (platform has already filtered by date range)
        # C#: // Format: FINAL_BAR|TF|Time|Open|High|Low|Close|Volume|SMA_O|SMA_H|SMA_L|SMA_C
        # C#: var line = $"FINAL_BAR|{tf}|{bar.OpenTime:yyyy-MM-dd HH:mm:ss}|{bar.Open.ToString(fmt, CultureInfo.InvariantCulture)}|{bar.High.ToString(fmt, CultureInfo.InvariantCulture)}|{bar.Low.ToString(fmt, CultureInfo.InvariantCulture)}|{bar.Close.ToString(fmt, CultureInfo.InvariantCulture)}|{bar.TickVolume}|{sO}|{sH}|{sL}|{sC}";
        # C#: Print(line);
        bar_time = bar.OpenTime.strftime("%Y-%m-%d %H:%M:%S")
        line = f"FINAL_BAR|{tf}|{bar_time}|{bar.Open:{fmt}}|{bar.High:{fmt}}|{bar.Low:{fmt}}|{bar.Close:{fmt}}|{bar.TickVolume}|{sO}|{sH}|{sL}|{sC}"
        self._log(line)
    
    def _log(self, message: str):
        """
        Log message to file (matching C# Print() behavior)
        NO stdout output - all output goes to log file
        """
        if self.log_file:
            # Format: timestamp | Info | message (matching C# log format)
            timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S.%f")[:-3]
            self.log_file.write(f"{timestamp} | Info | {message}\n")
            self.log_file.flush()
