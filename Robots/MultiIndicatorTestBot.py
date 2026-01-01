"""
Multi-Indicator Test Bot
Tests EMA, RSI, and Bollinger Bands together on H1 bars
"""
import os
from Api.KitaApi import KitaApi
from Api.Symbol import Symbol
from Indicators.ExponentialMovingAverage import ExponentialMovingAverage
from Indicators.RelativeStrengthIndex import RelativeStrengthIndex
from Indicators.Vidya import Vidya
from Indicators.MacdCrossOver import MacdCrossOver
from Indicators.MacdHistogram import MacdHistogram
from Indicators.BollingerBands import BollingerBands
from Api.KitaApiEnums import MovingAverageType


class MultiIndicatorTestBot(KitaApi):
    """Test bot to verify multiple indicators on H1 bars"""
    
    def __init__(self):
        super().__init__()
        self.symbol_name = "AUDNZD"
        self.active_symbol: Symbol = None  # type: ignore
        self.ema_indicator: ExponentialMovingAverage = None  # type: ignore
        self.rsi_indicator: RelativeStrengthIndex = None  # type: ignore
        self.bb_indicator: BollingerBands = None  # type: ignore
        self.vidya_indicator: Vidya = None  # type: ignore
        self.macd_cross: MacdCrossOver = None  # type: ignore
        self.macd_hist: MacdHistogram = None  # type: ignore
        self.log_file = None
        self.last_bar_time = None
        
    def on_init(self):
        """Initialize the bot and request H1 bars"""
        # Setup logging
        log_dir = r"C:\Users\HMz\Documents\cAlgo\Logfiles"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        log_path = os.path.join(log_dir, "MultiIndicator_Test_Python.csv")
        self.log_file = open(log_path, "w", encoding="utf-8")
        self.log_file.write("Date,Time,Close,EMA,RSI,BB_Main,Vidya,MACD,Signal,Hist\n")
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
            # MACD needs 26 periods (longest), so request 26+ bars
            # Note: request_bars is internal, not part of cTrader API
            self.active_symbol.request_bars(3600, 26)
            print("H1 bars requested")

    def on_start(self, symbol: Symbol) -> None:
        """Called when backtest starts for a specific symbol"""
        pass

    def on_tick(self, symbol: Symbol):
        """Main tick processing - logs H1 bar completion with all indicator values"""
        
        # Get H1 Bars using MarketData API
        bars = self.MarketData.GetBars(3600, self.symbol_name)
        if bars is None or bars.count == 0:
            return

        # Initialize indicators on first tick with bars using Indicators API
        if self.ema_indicator is None and bars.read_index >= 0:
            print(f"Initializing indicators at bar {bars.read_index}")
            
            # EMA(14)
            error, self.ema_indicator = self.Indicators.exponential_moving_average(bars.close_bids, 14)
            if error != "":
                print(f"Error creating EMA: {error}")
                return
            
            # RSI(14)
            error, self.rsi_indicator = self.Indicators.relative_strength_index(bars.close_bids, 14)
            if error != "":
                print(f"Error creating RSI: {error}")
                return
            
            # Bollinger Bands(20, 2.0)
            error, self.bb_indicator = self.Indicators.bollinger_bands(bars.close_bids, 20, 2.0, MovingAverageType.Simple)
            if error != "":
                print(f"Error creating Bollinger Bands: {error}")
                return
            
            # Vidya(14, 0.65)
            error, self.vidya_indicator = self.Indicators.vidya(bars.close_bids, 14, 0.65)
            if error != "":
                print(f"Error creating Vidya: {error}")
                return
            
            # MACD(26, 12, 9)
            error, self.macd_cross = self.Indicators.macd_cross_over(bars.close_bids, 26, 12, 9)
            if error != "":
                print(f"Error creating MACD CrossOver: {error}")
                return
            
            error, self.macd_hist = self.Indicators.macd_histogram(bars.close_bids, 26, 12, 9)
            if error != "":
                print(f"Error creating MACD Histogram: {error}")
                return
            
            # Calculate for all bars up to current read_index
            for i in range(bars.read_index + 1):
                self.ema_indicator.calculate(i)
                self.rsi_indicator.calculate(i)
                self.bb_indicator.calculate(i)
                self.vidya_indicator.calculate(i)
                self.macd_cross.calculate(i)
                self.macd_hist.calculate(i)
            
            print(f"All indicators initialized and calculated for {bars.read_index + 1} bars")

        # Get the current bar index
        index = bars.read_index
        if index < 0:
            return
            
        bar_time = bars.open_times.data[index]
        
        if bar_time is None:
            return
        
        # Only log when a new bar completes
        if self.last_bar_time is not None and bar_time == self.last_bar_time:
            return
        
        # Prevent logging historical bars before backtest start
        if bar_time < self._BacktestStartUtc:
            return

        self.last_bar_time = bar_time
        
        # Ensure indicators are calculated for this index
        self.ema_indicator.calculate(index)
        self.rsi_indicator.calculate(index)
        self.bb_indicator.calculate(index)
        self.vidya_indicator.calculate(index)
        self.macd_cross.calculate(index)
        self.macd_hist.calculate(index)
        
        # Get values
        close = bars.close_bids.data[index]
        ema_val = self.ema_indicator.result.data[index]
        rsi_val = self.rsi_indicator.result.data[index]
        bb_main = self.bb_indicator.main.data[index]
        vidya_val = self.vidya_indicator.result.data[index]
        macd_line = self.macd_cross.macd.data[index]
        macd_signal = self.macd_cross.signal.data[index]
        hist_val = self.macd_hist.difference.data[index]
        
        # Format and log
        import math
        def fmt(val):
            if val is None or math.isnan(val): return "NaN"
            return f"{val:.5f}"
        
        date_str = bar_time.strftime("%Y.%m.%d")
        time_str = bar_time.strftime("%H:%M")
        
        log_line = f"{date_str},{time_str},{fmt(close)},{fmt(ema_val)},{fmt(rsi_val)},{fmt(bb_main)},{fmt(vidya_val)},{fmt(macd_line)},{fmt(macd_signal)},{fmt(hist_val)}\n"
        self.log_file.write(log_line)
        self.log_file.flush()
        
        if index % 10 == 0:
            print(f"Bar {index}: {date_str} {time_str} | Close: {fmt(close)} | EMA: {fmt(ema_val)} | Vidya: {fmt(vidya_val)} | MACD: {fmt(macd_line)}")

    def on_stop(self, symbol: Symbol = None):
        """Cleanup when backtest ends"""
        if self.log_file:
            self.log_file.close()
        print("\nMulti-Indicator Test completed")
