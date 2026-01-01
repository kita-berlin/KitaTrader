"""
Test H1 Bars Creation and Bollinger Bands Indicator
Tests that H1 bars are created correctly and Bollinger Bands calculate properly
"""
import os
import pytz
from datetime import datetime
from Api.KitaApiEnums import *
from Robots.BollingerBandsTestBot import BollingerBandsTestBot
from BrokerProvider.QuoteCtraderCache import QuoteCtraderCache
from BrokerProvider.TradePaper import TradePaper

class TestH1BarsBB:
    def __init__(self):
        # 1. Set the parameters of the platform
        self.robot = BollingerBandsTestBot()

        # AllDataStartUtc and AllDataEndUtc will be calculated automatically based on indicator warm-up requirements
        # AllDataEndUtc defaults to max, will be set during initialization

        # Platform mode
        self.robot.RunningMode = RunMode.SilentBacktesting
        # Historical data path - using cTrader cache path
        # This path uses t1 subdirectory (not tick)
        self.robot.DataPath = r"C:\Users\HMz\AppData\Roaming\Spotware\Cache\pepperstone\BacktestingCache\V1\demo_19011fd1"
        
        # Quote Provider Configuration
        # QuoteCtraderCache expects {base_path}\{symbol}\t1\{YYYYMMDD}.zticks
        # So we pass the base path directly
        self.robot.quote_provider = QuoteCtraderCache(
            data_rate=0,  # Tick data
            parameter=self.robot.DataPath
        )

        # Trade Provider Configuration
        self.robot.trade_provider = TradePaper()

        # Preload data
        self.robot.DataMode = DataMode.Preload

        # Paper trading initial account settings
        self.robot.AccountInitialBalance = 10000
        self.robot.AccountLeverage = 500
        self.robot.AccountCurrency = "EUR"
        
        # 2. Define the backtest time window - December 2025
        self.robot.BacktestStartUtc = datetime.strptime("01.12.2025", "%d.%m.%Y").replace(tzinfo=pytz.UTC)
        self.robot.BacktestEndUtc = datetime.strptime("31.12.2025", "%d.%m.%Y").replace(tzinfo=pytz.UTC)

        # 3. Initialize the platform and the robot
        self.robot.do_init()

        # 4. Start the platform and the robot
        self.robot.do_start()

        # 5. Loop over the given time range
        import time
        start_time = time.time()
        tick_count = 0
        while True:
            tick_count += 1
            result = self.robot.do_tick()
            if result:
                break
        elapsed_time = time.time() - start_time
        print(f"\nTest completed: {tick_count:,} ticks processed in {elapsed_time:.2f} seconds", flush=True)

        # 6. Stop the robot and the platform
        self.robot.do_stop()


if __name__ == "__main__":
    TestH1BarsBB()

