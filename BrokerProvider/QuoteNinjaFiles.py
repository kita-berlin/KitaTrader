import os
import os.path
import clr
from datetime import datetime, timedelta
from lzma import LZMADecompressor, FORMAT_AUTO  # type: ignore
from Api.KitaApi import KitaApi, Symbol, Bars
from Api.QuoteProvider import QuoteProvider


class NinjaFiles(QuoteProvider):
    provider_name = "NinjaFiles"
    _assets_file_name: str = "Assets_NinjaFiles_Live.csv"

    def __init__(self, data_rate: int, parameter: str = ""):
        assets_path = os.path.join("Files", self._assets_file_name)
        QuoteProvider.__init__(self, parameter, assets_path, data_rate)

    def init_symbol(self, api: KitaApi, symbol: Symbol):
        self.api = api
        self.symbol = symbol
        clr.AddReference("path_to_your_dll/MyLibrary.dll")
        from NinjaFiles import GlobalOptions
        os.path.join(os.environ["USERPROFILE"], "Documents", "NinjaTrader 8", "db")

         GlobalOptions.HistoricalDataPath = "C:\Users\HMz\Documents\NinjaTrader 8\db"

         """
         DateTime startDateTime = new DateTime(2025, 1, 7);
         int numberDaysForward = 7;
         int numberDaysBack = 7;
         NCDFiles myFiles = new NCDFiles(NCDFileType.Minute,
            "NQ 03-25",
            startDateTime,
            numberDaysForward,
            numberDaysBack);

         while (!myFiles.EndOfData)
         {
            MinuteRecord record = (MinuteRecord)myFiles.ReadNextRecord();
            // do whatever you want with it
         }
        """

    def get_day_at_utc(self, utc: datetime) -> tuple[str, datetime, Bars]:
        day_data: Bars = []

        return "", self.last_utc, day_data

    def get_first_datetime(self) -> tuple[str, datetime]:
        start_date = datetime(2000, 1, 1)
        end_date = datetime.now()

        return self.get_day_at_utc(end_date + timedelta(days=1))

    def _get_file_name(self, cache_path: str, utc: datetime, symbol_name: str) -> str:
        return os.path.join(
            cache_path,
            symbol_name,
            "bi5",
            f"{utc.year:04}",
            f"{utc.month - 1:02}",
            f"{utc.day:02}",
            f"{utc.hour:02}h_ticks.bi5",
        )


# end of file
