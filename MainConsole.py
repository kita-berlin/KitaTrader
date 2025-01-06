from Api.CoFu import *
from Api.KitaApiEnums import *

from Robots.Template import Template  # type: ignore
from Robots.Downloader import Downloader  # type: ignore
from Robots.Template import Template  # type: ignore
from Robots.Ultron import Ultron  # type: ignore


class MainConsole:
    def __init__(self):
        # 1. Set the parameters of the platform
        # region
        self.robot = Template()  # Define here which robot should be used

        # self.robot.AllDataStartUtc = datetime.min means earliest possible what the source can provide
        # End datetime always is yesterday. Cannot be today because today's data are not complete yet
        self.robot.AllDataStartUtc = datetime.strptime("3.1.2006", "%d.%m.%Y")

        # Platform mode how the robot will be used by the platform
        # Other possibilities are (not yet implemented): RealTime (live trading),
        # VisualBacktesting, BruteForceOptimization, GeneticOptimization, WalkForwardOptimization
        self.robot.RunningMode = RunMode.SilentBacktesting

        # The path where the robot can store data
        self.robot.CachePath = "..\\QuantConnect\\MyLean\\MyData\\cfd"

        # Paper trading initial account settings
        self.robot.AccountInitialBalance = 10000
        self.robot.AccountLeverage = 500
        # until full currency conversion is implemented, the quote currency of the traded symbol is used as the account currency
        self.robot.AccountCurrency = "EUR"
        # endregion

        # 2. Set the parameters for the robot
        # region
        # Define the backtest time window
        self.robot.BacktestStartUtc = datetime.strptime("3.1.2024", "%d.%m.%Y")
        # self.robot.BacktestEndUtc = datetime.strptime("10.12.2024", "%d.%m.%Y")
        self.robot.BacktestEndUtc = datetime.max
        # self.robot.Parameter1 = 1.3
        # self.robot.Parameter2 = 0.29
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
