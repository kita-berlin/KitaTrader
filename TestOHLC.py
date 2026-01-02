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
        # Historical data path - using cTrader cache path (uses t1 subdirectory)
        self.robot.DataPath = r"C:\Users\HMz\AppData\Roaming\Spotware\Cache\pepperstone\BacktestingCache\V1\demo_19011fd1"
        
        # Quote Provider Configuration
        # Cache path structure: {base_path}\{symbol}\t1\{YYYYMMDD}.zticks
        self.robot.quote_provider = QuoteCtraderCache(
            data_rate=0,  # Tick data
            parameter=self.robot.DataPath
        )

        # Trade Provider Configuration
        self.robot.trade_provider = TradePaper()

        # Preload data for the whole period or load data during the backtest run
        self.robot.DataMode = DataMode.Preload

        # Paper trading initial account settings
        self.robot.AccountInitialBalance = 10000
        self.robot.AccountLeverage = 500
        self.robot.AccountCurrency = "EUR"
        # endregion
        
        # 2. Define the backtest time window
        # region
        # Test 3 days: 1.12.25 to 3.12.25 (inclusive)
        # BacktestStart/BacktestEnd are interpreted as UTC 00:00 (midnight UTC)
        # Set end to 06.12.2025 (04.12.2025 + 2 days) to allow Python to process more ticks
        self.robot.BacktestStart = datetime.strptime("01.12.2025", "%d.%m.%Y")
        self.robot.BacktestEnd = datetime.strptime("06.12.2025", "%d.%m.%Y")  # End date (exclusive, +2 days from C#)
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


