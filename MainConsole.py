from Api.AlgoApi import AlgoApi
from Api.Settings import *
from Api.CoFu import *


#############################################
class MainConsole:
    def __init__(self):
        trading = AlgoApi()
        trading.pre_start()
        trading.start()

        while True:
            if trading.tick():
                break

            reward = trading.calculate_reward(trading)
        pass

        trading.on_stop()


#############################################
MainConsole()  # starts main loop and does not return

# end of file