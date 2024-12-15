from Api.CoFu import *
from KitaApiEnums import *
from Template import Template


class MainConsole:
    def __init__(self):

        # 1. Set the parameters of the platform
        # region
        self.robot = Template()  # The robot to be used
        self.robot.robot = self.robot  # type:ignore

        self.robot.TickDataStartUtc = datetime.min  # means earliest possible
        #self.robot.TickDataStartUtc = datetime.strptime("3.1.2006", "%d.%m.%Y")

        #self.robot.TickDataEndUtc = datetime.max  # means latest possible
        self.robot.TickDataEndUtc = datetime.strptime("10.01.2006", "%d.%m.%Y")

        self.robot.RunningMode = RunMode.SilentBacktesting

        self.robot.AccountInitialBalance = 10000
        self.robot.AccountLeverage = 500
        # until full currency conversion is implemented, the quote currency of the traded symbol is used as the account currency
        self.robot.AccountCurrency = "EUR"
        # endregion

        # 2. Set the parameters of the robot
        # region
        # self.robot.Rebuy1stPercent = 1.0
        # self.robot.RebuyPercent = 0.1
        # self.robot.TakeProfitPercent = 0.1
        # self.robot.Volume = 1000
        self.robot.Direction = TradeDirection.Mode1
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
