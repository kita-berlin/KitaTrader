from datetime import datetime
from Api.CoFu import *
from KitaApiEnums import *
from Martingale import Martingale


class MainConsole:
    def __init__(self):

        # 1. Set the parameters of the platform
        # region
        self.robot = Martingale()
        self.robot.loaded_robot = self.robot  # type:ignore
        self.robot.StartUtc = datetime.strptime("2024-01-01", "%Y-%m-%d")
        self.robot.EndUtc = datetime.strptime("2030-01-01", "%Y-%m-%d")
        self.robot.RunningMode = RunMode.SilentBacktesting

        self.robot.AccountInitialBalance = 10000
        self.robot.AccountLeverage = 500
        self.robot.AccountCurrency = "EUR"
        # endregion

        # 2. Set the parameters of the self.robot
        # region
        self.robot.Rebuy1stPercent = 1.0
        self.robot.RebuyPercent = 0.1
        self.robot.TakeProfitPercent = 0.1
        self.robot.Volume = 1000
        self.robot.Direction = TradeDirection.Mode1
        # endregion

        # 3. Start the platform and the robot
        # region
        self.robot.start()  # type: ignore
        # endregion

        # 4. loop over the give time range
        # region
        while True:
            if self.robot.tick():
                break
        # endregion

        # 5. Stop the robot and the platform
        # region
        self.robot.stop()
        # endregion


MainConsole()  # starts the main loop

# end of file
