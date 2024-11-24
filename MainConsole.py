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
            today = datetime.now()
            settings = SystemSettings(
                "",  # data path
                "",  # symbol
                "2024-01-01",
                today.strftime("%Y-%m-%d"),
                "0",
                "0",
                "0",
                "0",  # volume
                0,  # visual mode
                0,  # speed
                "0",  # chart bars
                "0",  # timeframe value
                str(TimeframeUnits.sec).split(".")[1],
                Platform=Platform.me_files,
            )

        trading = AlgoApi(settings)
        trading.pre_start()
        trading.start()

        while True:
            if trading.Tick():
                break

            reward = trading.calculate_reward(trading)
        pass

        trading.on_stop()


#############################################
MainConsole()  # starts main loop and does not return

# end of file