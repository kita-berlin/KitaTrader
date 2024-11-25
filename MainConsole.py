import os
import os.path
from datetime import datetime
from Api.AlgoApi import AlgoApi
from Api.Settings import *
from Api.CoFu import *


#############################################
class MainConsole:
    def __init__(self):
        settings_path = os.path.join("Files", "System.json")
        error, settings = CoFu.load_settings(settings_path)
        if "" != error:
            # create empty sttings file
            settings = SystemSettings(
                "1",
                "2",
                "3",
                "4",
                "5",
                "6",
                "7",
                "8",
                "9",
                "10",
                "11",
                "12",
                "13",
                "14"
            )

        trading = AlgoApi(settings)
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