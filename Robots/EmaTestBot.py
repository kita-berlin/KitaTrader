"""
EMA Test Bot - Tests Exponential Moving Average on H1 bars
"""
import os
from Api.KitaApi import KitaApi
from Api.Symbol import Symbol
from Indicators.ExponentialMovingAverage import ExponentialMovingAverage


class EmaTestBot(KitaApi):
    """Test bot to verify EMA calculation on H1 bars"""
    
    def __init__(self):
        super().__init__()
        self.symbol_name = "AUDNZD"
        self.active_symbol: Symbol = None  # type: ignore
        self.ema_indicator: ExponentialMovingAverage = None  # type: ignore
        self.log_file = None
        self.last_bar_time = None
        
    def on_init(self):
        """Initialize the bot and request H1 bars"""
        # Setup logging
        log_dir = r"C:\Users\HMz\Documents\cAlgo\Logfiles"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        log_path = os.path.join(log_dir, "EMA_Test_Python.csv")
        self.log_file = open(log_path, "w", encoding="utf-8")
        self.log_file.write("Date,Time,Close,EMA14\n")
        self.log_file.flush()
        
        print(f"Logging to {log_path}")
        
        # Request symbol and H1 bars
        err, self.active_symbol = self.request_symbol(
            self.symbol_name, 
            self.quote_provider, 
            self.trade_provider
        )
        if err == "":
            # Request H1 bars with lookback for indicator warm-up
            # EMA needs 14 periods, so request 14+ bars
            # Note: request_bars is internal, not part of cTrader API
            self.active_symbol.request_bars(3600, 14)
            print("H1 bars requested - EMA will initialize on first tick")

    def on_start(self, symbol: Symbol) -> None:
        """Called when backtest starts for a specific symbol"""
        pass

    def on_tick(self, symbol: Symbol):
        """Main tick processing - logs H1 bar completion with EMA values"""
        
        # Get H1 Bars using MarketData API
        bars = self.MarketData.GetBars(3600, self.symbol_name)
        if bars is None or bars.count == 0:
            return

        # Initialize EMA on first tick with bars using Indicators API
        if self.ema_indicator is None and bars.count > 0:
            print(f"Initializing EMA(14) on {bars.count} H1 bars")
            error, self.ema_indicator = self.Indicators.exponential_moving_average(
                source=bars.close_bids,
                periods=14
            )
            if error != "" or self.ema_indicator is None:
                print(f"Error creating EMA: {error}")
                return
            # Calculate for all existing bars
            for i in range(bars.count):
                self.ema_indicator.calculate(i)
            print(f"EMA initialized and calculated for {bars.count} bars")

        # Get the last completed bar
        index = bars.count - 1
        bar_time = bars.open_times.data[index]
        
        # Skip if bar_time is None
        if bar_time is None:
            return
        
        # Only log when a new bar completes
        if self.last_bar_time is not None and bar_time == self.last_bar_time:
            return
        
        self.last_bar_time = bar_time
        
        # Calculate EMA for the latest bar
        self.ema_indicator.calculate(index)
        
        # Get values
        close = bars.close_bids.data[index]
        ema_value = self.ema_indicator.result.data[index]
        
        # Skip if any value is None or NaN
        import math
        if close is None or ema_value is None:
            return
        if math.isnan(ema_value):
            return
        
        # Format and log
        date_str = bar_time.strftime("%Y.%m.%d")
        time_str = bar_time.strftime("%H:%M")
        
        log_line = f"{date_str},{time_str},{close:.5f},{ema_value:.5f}\n"
        self.log_file.write(log_line)
        self.log_file.flush()
        
        # Also print to console for visibility
        print(f"Bar: {date_str} {time_str} | Close: {close:.5f} | EMA(14): {ema_value:.5f}")

    def on_stop(self, symbol: Symbol = None):
        """Cleanup when backtest ends"""
        if self.log_file:
            self.log_file.close()
        print("\nEMA Test completed")
