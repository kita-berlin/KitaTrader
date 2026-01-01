import os
import pytz
from datetime import datetime
from Api.KitaApiEnums import *
from Robots.Template import Template  # type: ignore
from Robots.Downloader import Downloader  # type: ignore
from Robots.Template import Template  # type: ignore
from Robots.Ultron import Ultron  # type: ignore
from Robots.NinjaFiles import NinjaFiles  # type: ignore
from Robots.KitaTester import KitaTester  # type: ignore
from Robots.PriceVerifyBot import PriceVerifyBot
from Robots.BollingerBandsTestBot import BollingerBandsTestBot
from Robots.EmaTestBot import EmaTestBot
from Robots.Kanga2 import Kanga2
from BrokerProvider.QuoteCtraderCache import QuoteCtraderCache
from BrokerProvider.TradePaper import TradePaper

class MainConsole:
    def __init__(self):
        # 1. Set the parameters of the platform
        # region
        self.robot = Kanga2()  # Define here which robot should be used

        # AllDataStartUtc and AllDataEndUtc will be calculated automatically based on indicator warm-up requirements
        # AllDataEndUtc defaults to max, will be set during initialization

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
        # Full December 2025 (for comparison with cTrader CLI)
        # BacktestStart/BacktestEnd are interpreted as UTC 00:00 (midnight UTC)
        # This matches cTrader CLI behavior where dates are interpreted as UTC 00:00
        self.robot.BacktestStart = datetime.strptime("01.12.2025", "%d.%m.%Y")
        self.robot.BacktestEnd = datetime.strptime("30.12.2025", "%d.%m.%Y")
        # endregion

        # 3. Initialize the platform and the robot
        # region
        self.robot.do_init()  # type: ignore
        # endregion

        # 4. Start the platform and the robot
        # region
        self.robot.do_start()  # type: ignore
        # endregion

        # 5. loop over the give time range
        # region
        import time
        start_time = time.time()
        tick_count = 0
        while True:
            tick_count += 1
            result = self.robot.do_tick()
            if result:
                break
        elapsed_time = time.time() - start_time
        print(f"\nBacktest completed: {tick_count:,} ticks processed in {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)", flush=True)
        print(f"Performance: {tick_count/elapsed_time:.0f} ticks/second", flush=True)
        # endregion

        # 6. Stop the robot and the platform
        # region
        self.robot.do_stop()
        # endregion


MainConsole()  # starts the main loop

# end of file
