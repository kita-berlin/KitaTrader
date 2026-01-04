"""
Test script to verify bar generation for M1, M5, H1, H4 timeframes
after DataSeries indexing changes
"""
import os
import sys
from datetime import datetime
from Api.KitaApi import KitaApi
from Api.Symbol import Symbol
from Api.KitaApiEnums import *

class BarTestBot(KitaApi):
    """Simple bot to test bar generation for different timeframes"""
    
    def __init__(self):
        super().__init__()
        self.symbol_name = "AUDNZD"
        self.m_bars_m1 = None
        self.m_bars_m5 = None
        self.m_bars_h1 = None
        self.m_bars_h4 = None
        
    def on_init(self):
        """Initialize bars for different timeframes"""
        print("Initializing bars for M1, M5, H1, H4...")
        
        # Request bars for different timeframes
        self.m_bars_m1 = self.MarketData.GetBars(self.symbol_name, TimeFrame.M1)
        self.m_bars_m5 = self.MarketData.GetBars(self.symbol_name, TimeFrame.M5)
        self.m_bars_h1 = self.MarketData.GetBars(self.symbol_name, TimeFrame.H1)
        self.m_bars_h4 = self.MarketData.GetBars(self.symbol_name, TimeFrame.H4)
        
        print(f"M1 bars initialized: count={self.m_bars_m1.count if self.m_bars_m1 else 0}")
        print(f"M5 bars initialized: count={self.m_bars_m5.count if self.m_bars_m5 else 0}")
        print(f"H1 bars initialized: count={self.m_bars_h1.count if self.m_bars_h1 else 0}")
        print(f"H4 bars initialized: count={self.m_bars_h4.count if self.m_bars_h4 else 0}")
        
    def on_tick(self):
        """Check bars on each tick"""
        # Print bar info periodically
        if hasattr(self, '_tick_count'):
            self._tick_count += 1
        else:
            self._tick_count = 0
            
        # Print every 1000 ticks
        if self._tick_count % 1000 == 0:
            self._print_bar_info()
    
    def _print_bar_info(self):
        """Print information about bars for all timeframes"""
        print("\n" + "="*80)
        print(f"Tick #{self._tick_count} - Bar Information")
        print("="*80)
        
        for tf_name, bars in [("M1", self.m_bars_m1), ("M5", self.m_bars_m5), 
                              ("H1", self.m_bars_h1), ("H4", self.m_bars_h4)]:
            if bars and bars.count > 0:
                print(f"\n{tf_name} Bars:")
                print(f"  Count: {bars.count}")
                print(f"  Size: {bars.size}")
                print(f"  Read Index: {bars.read_index}")
                
                # Check DataSeries add_count
                if bars.close_bids:
                    print(f"  CloseBids._add_count: {bars.close_bids._add_count}")
                    print(f"  CloseBids.data._add_count: {bars.close_bids.data._add_count}")
                    print(f"  CloseBids.data._count: {bars.close_bids.data._count}")
                
                # Show last few bars
                if bars.count > 0:
                    print(f"  Last 3 bars:")
                    for i in range(min(3, bars.count)):
                        idx = bars.count - 1 - i
                        if idx >= 0:
                            time = bars.open_times.last(i) if bars.open_times else None
                            close = bars.close_bids.last(i) if bars.close_bids else None
                            print(f"    [{i}] Time: {time}, Close: {close}")
            else:
                print(f"\n{tf_name} Bars: Not initialized or empty")
        
        print("="*80 + "\n")

if __name__ == '__main__':
    # Initialize bot
    bot = BarTestBot()
    bot.RunningMode = RunMode.SilentBacktesting
    bot.data_source = "QuantConnect"
    bot.symbol_name = "AUDNZD"
    
    # Set data path (adjust as needed)
    bot.DataPath = r"G:\Meine Ablage\ShareFile\RoadToSuccess - General\Historical Data - UTC\NinjaTrader\6B\QuantConnect Seconds"
    
    # Initialize
    bot.do_init()
    bot.do_start()
    
    # Run a few ticks to generate bars
    print("Running ticks to generate bars...")
    for i in range(10000):
        if bot.do_tick():
            break
        if i % 1000 == 0:
            print(f"Processed {i} ticks...")
    
    # Final bar check
    print("\n" + "="*80)
    print("FINAL BAR CHECK")
    print("="*80)
    bot._print_bar_info()
    
    bot.do_stop()
    print("Test complete!")
