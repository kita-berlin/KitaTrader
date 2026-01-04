"""
OHLC Test Console - Compare OHLC values between C# and Python
Runs OHLCTestBot to log all bar OHLC values
"""
import os
import pytz
from datetime import datetime
from Api.KitaApiEnums import *
from Robots.OHLCTestBot import OHLCTestBot
from BrokerProvider.QuoteCtraderCache import QuoteCtraderCache
from BrokerProvider.TradePaper import TradePaper


class TestOHLC:
    def __init__(self):
        # 1. Set the parameters of the platform
        # region
        self.robot = OHLCTestBot()  # Use OHLC test bot

        # Platform mode how the robot will be used by the platform
        self.robot.RunningMode = RunMode.SilentBacktesting
        
        
        # Python MUST use the same path to ensure both bots use identical data
        self.robot.DataPath = r"C:\Users\HMz\AppData\Roaming\Spotware\Cache\Spotware\BacktestingCache\V1\demo_19011fd1"
        
        # Quote Provider Configuration
        # Cache path structure: {base_path}\{symbol}\t1\{YYYYMMDD}.zticks
        self.robot.quote_provider = QuoteCtraderCache(
            data_rate=0,  # Tick data
            parameter=self.robot.DataPath
        )

        # Trade Provider Configuration
        self.robot.trade_provider = TradePaper()

        # Data is loaded day-by-day during backtest (Online mode only)

        # Paper trading initial account settings
        self.robot.AccountInitialBalance = 10000
        self.robot.AccountLeverage = 500
        self.robot.AccountCurrency = "EUR"
        # endregion
        
        # 2. Define the backtest time window
        # region
        
        
        # This is a 1-day test for quick comparison
        from datetime import timedelta
        # Start at beginning of Dec 1 (UTC timezone-aware)
        self.robot.BacktestStart = datetime.strptime("01.12.2025 00:00", "%d.%m.%Y %H:%M").replace(tzinfo=pytz.UTC)
        
        # Explicit warmup start date (Nov 24) to ensure indicators have enough data
        # This replaces auto-calculation and decouples data loading from backtest start
        self.robot.WarmupStart = datetime.strptime("24.11.2025", "%d.%m.%Y")
        
        # End at beginning of Dec 5 (exclusive, UTC timezone-aware) to capture Dec 4 data
        self.robot.BacktestEnd = datetime.strptime("05.12.2025 00:00", "%d.%m.%Y %H:%M").replace(tzinfo=pytz.UTC)

        # endregion

        # 3. Initialize the platform and the robot
        # region
        self.robot.do_init()  # type: ignore
        # endregion

        # 4. Start the platform and the robot
        # region
        self.robot.do_start()  # type: ignore
        # endregion

        # 5. Loop over the given time range
        # region
        import time
        start_time = time.time()
        tick_count = 0
        # All debug output goes to robot's debug log file, nothing to stdout
        while True:
            tick_count += 1
            if tick_count % 100000 == 0:
                self.robot._debug_log(f"Processed {tick_count:,} ticks...")
            result = self.robot.do_tick()
            if result:
                self.robot._debug_log(f"Tick loop ended after {tick_count:,} ticks")
                break
        elapsed_time = time.time() - start_time
        self.robot._debug_log(f"Backtest completed: {tick_count:,} ticks processed in {elapsed_time:.2f} seconds")
        # endregion

        # 6. Stop the robot and the platform
        # region
        self.robot.do_stop()
        # endregion


if __name__ == "__main__":
    TestOHLC()


