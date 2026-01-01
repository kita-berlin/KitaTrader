"""
Bollinger Bands Test Bot
Tests H1 bars over 10 days with Bollinger Bands indicator
"""
import os
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
        self.bb_indicator: BollingerBands = None  # type: ignore
        self.log_file = None
        self.last_bar_time = None
        
    def on_init(self):
        """Initialize the bot and request H1 bars"""
        # Setup logging
        log_dir = r"C:\Users\HMz\Documents\cAlgo\Logfiles"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        log_path = os.path.join(log_dir, "BollingerBands_Test_Python.csv")
        self.log_file = open(log_path, "w", encoding="utf-8")
        self.log_file.write("Date,Time,Close,BB_Main,BB_Top,BB_Bottom\n")
        self.log_file.flush()
        
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

    def on_start(self, symbol: Symbol) -> None:
        """Called when backtest starts for a specific symbol"""
        pass

    def on_tick(self, symbol: Symbol):
        """Main tick processing - logs H1 bar completion with BB values"""
        
        # Get H1 Bars using MarketData API
        bars = self.MarketData.GetBars(3600, self.symbol_name)
        if bars is None or bars.count == 0:
            return

        # Initialize indicator on first tick when bars are available using Indicators API
        if self.bb_indicator is None and bars.count >= 20:
            print(f"Initializing Bollinger Bands on {bars.count} H1 bars")
            # Create Bollinger Bands indicator using central Indicators API
            # C#: mBollinger = mBot.Indicators.BollingerBands(mBotBars.ClosePrices, 20, 2.0, MAType.Simple)
            error, self.bb_indicator = self.Indicators.bollinger_bands(
                source=bars.close_bids,
                periods=20,
                standard_deviations=2.0,
                ma_type=MovingAverageType.Simple,
                shift=0
            )
            if error != "" or self.bb_indicator is None:
                print(f"Error creating Bollinger Bands: {error}")
                return
            
            # Calculate for all existing bars (need at least periods bars)
            min_bars = max(self.bb_indicator.periods - 1, 0)
            for i in range(min_bars, bars.count):
                self.bb_indicator.calculate(i)
            
            print(f"Bollinger Bands initialized and calculated for {bars.count} bars")

        # Need indicator initialized and enough bars
        if self.bb_indicator is None:
            return
            
        # Need at least periods+1 bars for BB to have valid values
        if bars.count < self.bb_indicator.periods + 1:
            return

        # Log all completed bars (like cTrader's OnBar() which is called for each completed bar)
        # We need to log bars that have valid BB values
        # Start from the first bar with valid BB (periods - 1) and log up to the previous completed bar
        min_log_index = max(self.bb_indicator.periods - 1, 0)
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
        for index in range(start_idx, max_log_index + 1):
            if index < 0 or index >= bars.count or index < min_log_index:
                continue
                
            bar_time = bars.open_times.data[index] if index < len(bars.open_times.data) else None
            if bar_time is None:
                continue
        
            # Calculate BB for this bar if not already calculated
            self.bb_indicator.calculate(index)
            
            # Get values using direct index access
            if index >= len(bars.close_bids.data):
                continue
            close = bars.close_bids.data[index]
            
            # Get BB values
            bb_main = self.bb_indicator.main.data[index] if index < len(self.bb_indicator.main.data) else float('nan')
            bb_top = self.bb_indicator.top.data[index] if index < len(self.bb_indicator.top.data) else float('nan')
            bb_bottom = self.bb_indicator.bottom.data[index] if index < len(self.bb_indicator.bottom.data) else float('nan')
            
            # Skip if any value is None or NaN
            import math
            if close is None or math.isnan(close):
                continue
            if math.isnan(bb_main) or math.isnan(bb_top) or math.isnan(bb_bottom):
                continue  # Skip bars without valid BB values
            
            # Only log bars within the backtest period (matching cTrader behavior)
            if bar_time < self.BacktestStartUtc or bar_time >= self.BacktestEndUtc:
                continue  # Skip bars outside backtest period
            
            # Format and log
            date_str = bar_time.strftime("%Y.%m.%d")
            time_str = bar_time.strftime("%H:%M")
            
            log_line = f"{date_str},{time_str},{close:.5f},{bb_main:.5f},{bb_top:.5f},{bb_bottom:.5f}\n"
            self.log_file.write(log_line)
            logged_any = True
            
            # Update last logged bar time
            self.last_bar_time = bar_time
        
        # Flush after logging all new bars
        if logged_any:
            self.log_file.flush()

    def on_stop(self, symbol: Symbol = None):
        """Cleanup when backtest ends"""
        if self.log_file:
            self.log_file.close()
        print("\nBollinger Bands Test completed")
