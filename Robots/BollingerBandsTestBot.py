"""
Bollinger Bands Test Bot
Tests H1 bars over 10 days with Bollinger Bands indicator
"""
import os
import sys
from Api.KitaApi import KitaApi
from Api.Symbol import Symbol
from Indicators.BollingerBands import BollingerBands
from Api.KitaApiEnums import MovingAverageType


class BollingerBandsTestBot(KitaApi):
    """Test bot to verify Bollinger Bands calculation on H1 bars"""
    
    def __init__(self):
        super().__init__()
        self.symbol_name = "AUDNZD"
        self.active_symbol: Symbol = None  # type: ignore
        self.bb_open: BollingerBands = None  # type: ignore
        self.bb_high: BollingerBands = None  # type: ignore
        self.bb_low: BollingerBands = None  # type: ignore
        self.bb_close: BollingerBands = None  # type: ignore
        self.log_file = None
        self.debug_log_file = None
        self.last_bar_time = None
        self.last_printed_date = None  # Track last printed date for progress
        
    def _debug_log(self, message: str):
        """Write debug message to debug log file"""
        if self.debug_log_file:
            self.debug_log_file.write(f"{message}\n")
            self.debug_log_file.flush()
        
    def on_init(self):
        """Initialize the bot and request H1 bars"""
        # Setup logging
        log_dir = r"C:\Users\HMz\Documents\cAlgo\Logfiles"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        log_path = os.path.join(log_dir, "BollingerBands_Test_Python.csv")
        self.log_file = open(log_path, "w", encoding="utf-8")
        self.log_file.write("Date,Time,Open,High,Low,Close,BB_Open_Main,BB_Open_Top,BB_Open_Bottom,BB_High_Main,BB_High_Top,BB_High_Bottom,BB_Low_Main,BB_Low_Top,BB_Low_Bottom,BB_Close_Main,BB_Close_Top,BB_Close_Bottom\n")
        self.log_file.flush()
        
        # Setup debug logging
        debug_log_path = os.path.join(log_dir, "BollingerBands_Test_Python_Debug.log")
        self.debug_log_file = open(debug_log_path, "w", encoding="utf-8")
        self._debug_log("BollingerBandsTestBot: on_init() called")
        self._debug_log(f"BollingerBandsTestBot: Log file opened: {log_path}")
        self._debug_log(f"BollingerBandsTestBot: Debug log file opened: {debug_log_path}")
        
        # Request symbol and H1 bars (indicator will be initialized in on_tick when bars are available)
        err, self.active_symbol = self.request_symbol(
            self.symbol_name, 
            self.quote_provider, 
            self.trade_provider
        )
        if err == "":
            # Request H1 bars (3600 seconds) with lookback for indicator warm-up
            # Bollinger Bands needs 20 periods, so request 20+ bars
            # Note: request_bars is internal, not part of cTrader API
            self.active_symbol.request_bars(3600, 20)
            self._debug_log(f"BollingerBandsTestBot: Requested H1 bars for {self.symbol_name}")
        else:
            self._debug_log(f"BollingerBandsTestBot: Error requesting symbol: {err}")

    def on_start(self, symbol: Symbol) -> None:
        """Called when backtest starts for a specific symbol"""
        pass

    def on_tick(self, symbol: Symbol):
        """Main tick processing - logs H1 bar completion with BB values"""
        
        # Get H1 Bars using MarketData API
        bars = self.MarketData.GetBars(3600, self.symbol_name)
        if bars is None or bars.count == 0:
            return

        # Debug: Log first few ticks to see if on_tick is being called
        if not hasattr(self, '_tick_debug_count'):
            self._tick_debug_count = 0
        self._tick_debug_count += 1
        if self._tick_debug_count <= 3:
            self._debug_log(f"BollingerBandsTestBot: on_tick() called (tick #{self._tick_debug_count}), bars.count={bars.count}")

        # Initialize indicators on first tick when bars are available using Indicators API
        if self.bb_close is None and bars.count >= 20:
            self._debug_log(f"Initializing Bollinger Bands on all OHLC values for {bars.count} H1 bars")
            periods = 20
            std_dev = 2.0
            
            # Create Bollinger Bands on Open
            error, self.bb_open = self.Indicators.bollinger_bands(
                source=bars.open_bids,
                periods=periods,
                standard_deviations=std_dev,
                ma_type=MovingAverageType.Simple,
                shift=0
            )
            if error != "":
                self._debug_log(f"Error creating BB on Open: {error}")
            
            # Create Bollinger Bands on High
            error, self.bb_high = self.Indicators.bollinger_bands(
                source=bars.high_bids,
                periods=periods,
                standard_deviations=std_dev,
                ma_type=MovingAverageType.Simple,
                shift=0
            )
            if error != "":
                self._debug_log(f"Error creating BB on High: {error}")
            
            # Create Bollinger Bands on Low
            error, self.bb_low = self.Indicators.bollinger_bands(
                source=bars.low_bids,
                periods=periods,
                standard_deviations=std_dev,
                ma_type=MovingAverageType.Simple,
                shift=0
            )
            if error != "":
                self._debug_log(f"Error creating BB on Low: {error}")
            
            # Create Bollinger Bands on Close
            error, self.bb_close = self.Indicators.bollinger_bands(
                source=bars.close_bids,
                periods=periods,
                standard_deviations=std_dev,
                ma_type=MovingAverageType.Simple,
                shift=0
            )
            if error != "":
                self._debug_log(f"Error creating BB on Close: {error}")
            
            if self.bb_open and self.bb_high and self.bb_low and self.bb_close:
                self._debug_log(f"Bollinger Bands initialized on all OHLC (will be calculated during ticks): {bars.count} bars available")
            else:
                self._debug_log(f"Warning: Some Bollinger Bands indicators failed to initialize")

        # Need all indicators initialized and enough bars
        if not (self.bb_open and self.bb_high and self.bb_low and self.bb_close):
            return
            
        # Need at least periods+1 bars for BB to have valid values
        if bars.count < 21:
            return

        # Log all completed bars (like cTrader's OnBar() which is called for each completed bar)
        # We need to log bars that have valid BB values
        # Start from the first bar with valid BB (periods - 1) and log up to the previous completed bar
        min_log_index = max(19, 0)  # periods - 1 = 20 - 1 = 19
        max_log_index = bars.count - 2 if bars.count >= 2 else bars.count - 1  # Previous completed bar
        
        # Log all bars from last_logged_index to max_log_index
        if self.last_bar_time is None:
            # First time - log all available completed bars
            start_idx = min_log_index
        else:
            # Find the index of the last logged bar and continue from there
            start_idx = None
            for i in range(bars.count - 1, -1, -1):
                if i < len(bars.open_times.data) and bars.open_times.data[i] == self.last_bar_time:
                    start_idx = i + 1  # Start from next bar
                    break
            if start_idx is None:
                start_idx = min_log_index  # Fallback: start from beginning
        
        # Log all new completed bars
        logged_any = False
        bars_processed = 0
        for index in range(start_idx, max_log_index + 1):
            if index < 0 or index >= bars.count or index < min_log_index:
                continue
                
            bar_time = bars.open_times.data[index] if index < len(bars.open_times.data) else None
            if bar_time is None:
                continue
        
            bars_processed += 1
            
            # Get OHLC values using direct index access
            if index >= len(bars.open_bids.data) or index >= len(bars.close_bids.data):
                continue
            open_val = bars.open_bids.data[index]
            high_val = bars.high_bids.data[index]
            low_val = bars.low_bids.data[index]
            close_val = bars.close_bids.data[index]
            
            # Get BB values for all OHLC
            import math
            
            # BB on Open
            bb_open_main = self.bb_open.main.data[index] if index < len(self.bb_open.main.data) else float('nan')
            bb_open_top = self.bb_open.top.data[index] if index < len(self.bb_open.top.data) else float('nan')
            bb_open_bottom = self.bb_open.bottom.data[index] if index < len(self.bb_open.bottom.data) else float('nan')
            
            # BB on High
            bb_high_main = self.bb_high.main.data[index] if index < len(self.bb_high.main.data) else float('nan')
            bb_high_top = self.bb_high.top.data[index] if index < len(self.bb_high.top.data) else float('nan')
            bb_high_bottom = self.bb_high.bottom.data[index] if index < len(self.bb_high.bottom.data) else float('nan')
            
            # BB on Low
            bb_low_main = self.bb_low.main.data[index] if index < len(self.bb_low.main.data) else float('nan')
            bb_low_top = self.bb_low.top.data[index] if index < len(self.bb_low.top.data) else float('nan')
            bb_low_bottom = self.bb_low.bottom.data[index] if index < len(self.bb_low.bottom.data) else float('nan')
            
            # BB on Close
            bb_close_main = self.bb_close.main.data[index] if index < len(self.bb_close.main.data) else float('nan')
            bb_close_top = self.bb_close.top.data[index] if index < len(self.bb_close.top.data) else float('nan')
            bb_close_bottom = self.bb_close.bottom.data[index] if index < len(self.bb_close.bottom.data) else float('nan')
            
            # Skip if any OHLC value is None or NaN
            if (open_val is None or math.isnan(open_val) or 
                high_val is None or math.isnan(high_val) or
                low_val is None or math.isnan(low_val) or
                close_val is None or math.isnan(close_val)):
                continue
            
            # Skip if any BB value is NaN (not enough data yet)
            if (math.isnan(bb_open_main) or math.isnan(bb_open_top) or math.isnan(bb_open_bottom) or
                math.isnan(bb_high_main) or math.isnan(bb_high_top) or math.isnan(bb_high_bottom) or
                math.isnan(bb_low_main) or math.isnan(bb_low_top) or math.isnan(bb_low_bottom) or
                math.isnan(bb_close_main) or math.isnan(bb_close_top) or math.isnan(bb_close_bottom)):
                continue  # Skip bars without valid BB values
            
            # Print progress: show date only when it changes (including first day)
            # Print before filtering so we see progress even if bar is filtered
            date_str = bar_time.strftime("%Y.%m.%d")
            if self.last_printed_date is None or self.last_printed_date != date_str:
                print(date_str, flush=True)
                self.last_printed_date = date_str
            
            # Only log bars within the backtest period (matching cTrader behavior)
            if bar_time < self._BacktestStartUtc or bar_time >= self._BacktestEndUtc:
                continue  # Skip bars outside backtest period
            
            # Format and log
            time_str = bar_time.strftime("%H:%M")
            
            log_line = (f"{date_str},{time_str},"
                       f"{open_val:.5f},{high_val:.5f},{low_val:.5f},{close_val:.5f},"
                       f"{bb_open_main:.5f},{bb_open_top:.5f},{bb_open_bottom:.5f},"
                       f"{bb_high_main:.5f},{bb_high_top:.5f},{bb_high_bottom:.5f},"
                       f"{bb_low_main:.5f},{bb_low_top:.5f},{bb_low_bottom:.5f},"
                       f"{bb_close_main:.5f},{bb_close_top:.5f},{bb_close_bottom:.5f}\n")
            self.log_file.write(log_line)
            logged_any = True
            
            # Update last logged bar time
            self.last_bar_time = bar_time
        
        # Flush after logging all new bars
        if logged_any:
            self.log_file.flush()
        
        # Debug: Log when we process bars
        if bars_processed > 0 and not hasattr(self, '_bars_debug_printed'):
            self._debug_log(f"BollingerBandsTestBot: Processing bars (processed {bars_processed} bars in this tick)")
            self._bars_debug_printed = True

    def on_stop(self, symbol: Symbol = None):
        """Cleanup when backtest ends"""
        if self.log_file:
            self.log_file.close()
        if self.debug_log_file:
            self._debug_log("Bollinger Bands Test completed")
            self.debug_log_file.close()
