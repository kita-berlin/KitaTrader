#import json
#import commentjson  # type: ignore
import pytz
from tzlocal import get_localzone  # type: ignore
from datetime import datetime


################## Common Functions #################
class CoFu:
    """
    @staticmethod
    def load_settings(path: str) -> tuple[str, StrSettings]:
        try:
            with open(path, "r") as file:
                settings = commentjson.load(  # pylint: disable=no-member # type: ignore
                    file
                )
                ret_val = StrSettings(**settings)
                return "", ret_val

        except FileNotFoundError:
            return path + " not found", None  # type: ignore

        except Exception as e:
            return "Fehler" + str(e), None  # type: ignore

    @staticmethod
    def save_settings(path: str, settings: StrSettings):
        try:
            with open(path, "w") as file:
                file.write(json.dumps(settings.__dict__, indent=4))

        except Exception:
            pass
    """

    @staticmethod
    def get_utc_time_from_local_time(localTime: datetime) -> datetime:
        local_time_with_tz = localTime.astimezone(get_localzone())  # type: ignore
        return local_time_with_tz.astimezone(pytz.utc)


# end of file
