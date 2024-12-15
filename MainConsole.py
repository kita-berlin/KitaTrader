from Api.CoFu import *
from KitaApiEnums import *
from Template import Template


class MainConsole:
    def __init__(self):

        # 1. Set the parameters of the platform
        # region
        self.robot = Template()  # Define here which robot should be used
        self.robot.robot = self.robot  # type:ignore

        #self.robot.AllDataStartUtc = datetime.min  # means earliest possible what the source can provide
        self.robot.AllDataStartUtc = datetime.strptime("3.1.2006", "%d.%m.%Y")

        # Platform mode how the robot will be used by the platform
        # Other possibilities are (not yet implemented): RealTime (live trading),
        # VisualBacktesting, BruteForceOptimization, GeneticOptimization, WalkForwardOptimization
        self.robot.RunningMode = RunMode.SilentBacktesting

        # Paper trading initial account settings
        self.robot.AccountInitialBalance = 10000
        self.robot.AccountLeverage = 500
        # until full currency conversion is implemented, the quote currency of the traded symbol is used as the account currency
        self.robot.AccountCurrency = "EUR"
        # endregion

        # 2. Set the parameters for the robot
        # region
        # Define the backtest time window
        self.robot.BacktestStartUtc = datetime.strptime("1.1.2023", "%d.%m.%Y")
        self.robot.BacktestEndUtc = datetime.max  # means latest possible
        # self.robot.Parameter1 = 1.3
        # self.robot.Parameter2 = 0.29
        # Both (means long and short trades will be done)
        self.robot.Direction = TradeDirection.Both
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
