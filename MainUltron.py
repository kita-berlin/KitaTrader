"""
Ultron Strategy - Main Runner for KitaTrader
Clean execution without BTGym/Backtrader overhead
"""

from datetime import datetime
from Api.KitaApiEnums import *
from Robots.Ultron import Ultron


class MainUltron:
    def __init__(self):
        print("\n" + "="*70)
        print("Ultron Strategy - KitaTrader Execution")
        print("="*70)
        print("\nMulti-Moving Average Strategy:")
        print("  - 4 Moving Averages (WMA + SMA)")
        print("  - Dynamic entry based on MA relationships")
        print("  - Automatic bid/ask execution")
        print("  - Take profit & stop loss management (tick-based)")
        print("="*70 + "\n")
        
        # Initialize robot
        self.robot = Ultron()
        
        # CRITICAL: Force QuantConnect settings BEFORE platform initialization
        self.robot.data_source = "QuantConnect"  # Force QuantConnect provider
        self.robot.symbol_name = "GBPUSD"        # Force GBPUSD symbol
        
        # Configure platform
        # Data range: Testing with shorter period for initial run
        # Weekend days will be automatically skipped by QuantConnect provider
        self.robot.AllDataStartUtc = datetime.strptime("18.03.2024", "%d.%m.%Y")
        
        # Backtest window: Full month (March 18 - April 18, 2024)
        # One month of trading to see actual performance
        self.robot.BacktestStartUtc = datetime.strptime("18.03.2024", "%d.%m.%Y")
        self.robot.BacktestEndUtc = datetime.strptime("18.04.2024", "%d.%m.%Y")
        
        # Platform mode
        self.robot.RunningMode = RunMode.SilentBacktesting
        
        # Data configuration
        # QuantConnect: Base path (provider adds QuoteQuantConnect/minute/GBPUSD/ subdirectories)
        # The data has been organized into: DataPath/QuoteQuantConnect/minute/GBPUSD/*.zip
        # For Dukascopy alternative: use "$(OneDrive)/KitaData/cfd"
        self.robot.DataPath = r"G:\Meine Ablage\ShareFile\RoadToSuccess - General\Historical Data - UTC\NinjaTrader\6B\QuantConnect Seconds"
        self.robot.DataMode = DataMode.Preload
        
        # Account settings
        self.robot.AccountInitialBalance = 10000.0
        self.robot.AccountLeverage = 500
        self.robot.AccountCurrency = "EUR"
        
        # Debug: Print what we're using
        print(f"DEBUG: data_source = {self.robot.data_source}")
        print(f"DEBUG: symbol_name = {self.robot.symbol_name}")
        print(f"DEBUG: DataPath = {self.robot.DataPath}")
        
        print("="*70)
        print("Running backtest...")
        print("="*70 + "\n")
        
        # Initialize the platform and robot
        self.robot.do_init()
        
        # Start the robot
        self.robot.do_start()
        
        # Run tick loop
        tick_count = 0
        while True:
            if self.robot.do_tick():
                break
            tick_count += 1
            
            # Progress indicator (every 10,000 ticks)
            if tick_count % 10000 == 0:
                print(f"Processed {tick_count:,} ticks...")
        
        # Stop the robot
        self.robot.do_stop()
        
        print("\n" + "="*70)
        print("BACKTEST COMPLETE!")
        print("="*70)


if __name__ == '__main__':
    MainUltron()

# End of file

