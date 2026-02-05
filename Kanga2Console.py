import os
import pytz
from datetime import datetime
from Api.KitaApiEnums import *
from Robots.Kanga2 import Kanga2
from BrokerProvider.QuoteCtraderCache import QuoteCtraderCache
from BrokerProvider.TradePaper import TradePaper

class MainConsole:
    def __init__(self):
        # 1. Set the parameters of the platform
        # region
        self.robot = Kanga2()  # Define here which robot should be used

        # Platform mode how the robot will be used by the platform
        self.robot.RunningMode = RunMode.SilentBacktesting

        # Historical data path - using cTrader cache path (uses t1 subdirectory)
        self.robot.DataPath = r"C:\Users\HMz\AppData\Roaming\Spotware\Cache\Spotware\BacktestingCache\V1\demo_19011fd1"
        
        # Quote Provider Configuration
        self.robot.quote_provider = QuoteCtraderCache(
            data_rate=0,  # Tick data
            parameter=self.robot.DataPath,
            credentials = r"C:\Users\HMz\Documents\Source\cTraderTools\Apps\PyDownload\env.txt"
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
        # BacktestStart/BacktestEnd are interpreted as UTC 00:00 (midnight UTC)
        # This matches cTrader CLI behavior where dates are interpreted as UTC 00:00
        # Time range: 01.12.2025 to 06.01.2026 (matching C# bot)
        self.robot.WarmupStart = datetime.strptime("24.11.2025", "%d.%m.%Y")
        self.robot.BacktestStart = datetime.strptime("01.12.2025", "%d.%m.%Y")
        # Set to 06.01.2026 (date only) - framework will convert to end of day (23:59:59.999)
        self.robot.BacktestEnd = datetime.strptime("06.01.2026", "%d.%m.%Y")  # End of day (inclusive)
        # endregion
        
        # Enable logging for comparison
        self.robot.is_do_logging = True
        
        # Load config file to match C# bot parameters
        # Use the same config file as C# bot: "Kanga2, AUDNZD h1 Long.cbotset"
        self.robot.config_path = r"G:\Meine Ablage\ConfigFiles\Kanga2"
        # Set symbol to match config (will be loaded from config file)
        self.robot.symbol_csv_all_visual = "AUDNZD"

        # 3. Initialize the platform and the robot
        # region
        self.robot._debug_log("[DEBUG] Starting do_init()...")
        self.robot.do_init()  # type: ignore
        self.robot._debug_log("[DEBUG] do_init() completed")
        # endregion

        # 4. Start the platform and the robot
        # region
        self.robot._debug_log("[DEBUG] Starting do_start()...")
        self.robot.do_start()  # type: ignore
        self.robot._debug_log("[DEBUG] do_start() completed")
        # endregion

        # 5. loop over the give time range
        # region
        import time
        start_time = time.time()
        tick_count = 0
        self.robot._debug_log("[DEBUG] Starting tick loop...")
        while True:
            tick_count += 1
            if tick_count % 100000 == 0:
                self.robot._debug_log(f"[DEBUG] Processed {tick_count:,} ticks...")
            result = self.robot.do_tick()
            if result:
                self.robot._debug_log(f"[DEBUG] Tick loop ended after {tick_count:,} ticks")
                break
        elapsed_time = time.time() - start_time
        self.robot._debug_log(f"Backtest completed: {tick_count:,} ticks processed in {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
        self.robot._debug_log(f"Performance: {tick_count/elapsed_time:.0f} ticks/second")
        # endregion

        # 6. Stop the robot and the platform
        # region
        self.robot.do_stop()
        # endregion


MainConsole()  # starts the main loop

# end of file
