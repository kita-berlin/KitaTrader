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


class OHLCTestConsole:
    def __init__(self):
        # 1. Set the parameters of the platform
        # region
        self.robot = OHLCTestBot()  # Use OHLC test bot

        # Platform mode how the robot will be used by the platform
        self.robot.RunningMode = RunMode.SilentBacktesting
        
        # Historical data path - using cTrader cache path
        # Assuming the standard Spotware cache location
        self.robot.DataPath = r"C:\Users\HMz\AppData\Roaming\Spotware\Cache\Spotware\BacktestingCache\V1\demo_19011fd1"
        
        # Quote Provider Configuration with automatic data download capability
        self.robot.quote_provider = QuoteCtraderCache(
            data_rate=0,  # Tick data
            parameter=self.robot.DataPath,
            # Credentials for downloading data if missing
            credentials=r"C:\Users\HMz\Documents\Source\cTraderTools\Apps\PyDownload\env.txt"
        )

        # Trade Provider Configuration
        self.robot.trade_provider = TradePaper()

        # Paper trading initial account settings
        self.robot.AccountInitialBalance = 10000
        self.robot.AccountLeverage = 500
        self.robot.AccountCurrency = "EUR"
        # endregion
        
        # 2. Define the backtest time window
        # region
        # Date range: 1 day only (Dec 1, 2025) - EXACTLY matching C# bot
        # C# bot runs Dec 1 only (00:00:00 to 23:59:59)
        from datetime import timedelta

        self.robot.WarmupStart = datetime.strptime("24.11.2025", "%d.%m.%Y")
        self.robot.BacktestStart = datetime.strptime("01.12.2025", "%d.%m.%Y")
        # Set to Dec 1 (date only) - framework will convert to Dec 2 00:00:00 (exclusive)
        # This ensures we get all bars from Dec 1 00:00:00 to Dec 1 23:59:59, matching C# exactly
        self.robot.BacktestEnd = datetime.strptime("01.12.2025", "%d.%m.%Y")  # Dec 1 only (inclusive)
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
        try:
            while True:
                tick_count += 1
                if tick_count % 100000 == 0:
                    self.robot._debug_log(f"Processed {tick_count:,} ticks...")
                result = self.robot.do_tick()
                if result:
                    self.robot._debug_log(f"Tick loop ended after {tick_count:,} ticks")
                    break
        except KeyboardInterrupt:
             self.robot._debug_log(f"Backtest interrupted by user.")       
        
        elapsed_time = time.time() - start_time
        self.robot._debug_log(f"Backtest completed: {tick_count:,} ticks processed in {elapsed_time:.2f} seconds")
        # endregion

        # 6. Stop the robot and the platform
        # region
        self.robot.do_stop()
        # endregion


if __name__ == "__main__":
    if "twisted.internet.reactor" in os.environ:
         # Prevent potential reactor conflict if imported elsewhere
         pass
    OHLCTestConsole()
