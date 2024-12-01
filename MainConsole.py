from datetime import datetime
from Api.AlgoApi import AlgoApi, RunningMode, Account
from Api.CoFu import *
from AlgoApiEnums import *


#############################################
class MainConsole:
    def __init__(self):
        account = Account()
        account.balance = account.equity = 10000
        account.leverage = 500
        account.asset = "EUR"

        algo_api = AlgoApi()
        algo_api.account = account
        algo_api.start_dt = datetime.strptime("2024-01-01", "%Y-%m-%d")
        algo_api.end_dt = datetime.strptime("2030-01-01", "%Y-%m-%d")
        algo_api.running_mode = RunningMode.SilentBacktesting
        algo_api.robot_name = "Martingale"
        # These parameters must also be declarated in the bot
        algo_api.robot_parameter = {
            "Rebuy1stPercent": 1.1,
            "RebuyPercent": 0.1,
            "TakeProfitPercent": 0.1,
            "Volume": 1000,
            "TradeDirection": TradeDirection.Mode1,
        }

        algo_api.start()

        while True:
            if algo_api.tick():
                break

        algo_api.stop()


#############################################
MainConsole()  # starts main loop and does not return

# end of file