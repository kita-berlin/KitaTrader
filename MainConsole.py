from datetime import datetime
from Api.KitaApiEnums import *
from Robots.Template import Template  # type: ignore
from Robots.Downloader import Downloader  # type: ignore
from Robots.Template import Template  # type: ignore
from Robots.Ultron import Ultron  # type: ignore
from Robots.NinjaFiles import NinjaFiles  # type: ignore
from Robots.KitaTester import KitaTester  # type: ignore


class MainConsole:
    def __init__(self):
        # 1. Set the parameters of the platform
        # region
        self.robot = KitaTester()  # Define here which robot should be used

        # self.robot.AllDataStartUtc = datetime.min means earliest possible what the source can provide
        # End datetime always is yesterday. Cannot be today because today's data are not complete yet
        self.robot.AllDataStartUtc = datetime.strptime("5.12.2024", "%d.%m.%Y")
        # self.robot.AllDataStartUtc = datetime.min

        # Platform mode how the robot will be used by the platform
        # Other possibilities are (not yet implemented): RealTime (live trading),
        # VisualBacktesting, BruteForceOptimization, GeneticOptimization, WalkForwardOptimization
        self.robot.RunningMode = RunMode.SilentBacktesting

        # Historical data path
        self.robot.DataPath = "$(OneDrive)/KitaData/cfd"

        # Paper trading initial account settings
        self.robot.AccountInitialBalance = 10000
        self.robot.AccountLeverage = 500
        # until full currency conversion is implemented, the quote currency of the traded symbol is used as the account currency
        self.robot.AccountCurrency = "EUR"
        # endregion

        # 2. Define the backtest time window
        # region
        # self.robot.BacktestStartUtc = datetime.min
        self.robot.BacktestStartUtc = datetime.strptime("3.1.2025", "%d.%m.%Y")

        # self.robot.BacktestEndUtc = datetime.strptime("10.12.2024", "%d.%m.%Y")
        self.robot.BacktestEndUtc = datetime.max
        # endregion

        # 3. Initialize the platform and the robot
        # region
        self.robot.init()  # type: ignore
        # endregion

        # 4. Start the platform and the robot
        # region
        self.robot.start()  # type: ignore
        # endregion

        # 5. loop over the give time range
        # region
        while True:
            if self.robot.tick():
                break
        # endregion

        # 6. Stop the robot and the platform
        # region
        self.robot.stop()
        # endregion


MainConsole()  # starts the main loop

# end of file
