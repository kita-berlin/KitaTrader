from Api.KitaApiEnums import *
from Api.KitaApi import KitaApi, Symbol
from Api.CoFu import *
from Api.Constants import *
from BrokerProvider.TradePaper import TradePaper
from BrokerProvider.QuoteDukascopy import Dukascopy  # type: ignore
from BrokerProvider.QuoteTradeMt5 import BrokerMt5  # type: ignore
from BrokerProvider.QuoteCsv import QuoteCsv  # type: ignore


class Downloader(KitaApi):

    # History
    # region
    version: str = "Downloader V1.0"
    # V1.0     03.01.25     HMz created
    # endregion

    # Members
    # region
    symbols_to_load: list[str] = [
        # "GBPUSD",
        # "EURUSD",
        "NZDCAD",
        # "AUDCAD",
        # "DEU.IDX_EUR",
        # "USA30.IDX_USD",
        # "USATECH.IDX_USD",
        # "USA500.IDX_USD",
        # "XAUUSD",
    ]

    def __init__(self):
        super().__init__()  # Importatnt, do not delete

    # endregion

    ###################################
    def on_init(self) -> None:
        # self.robot.AllDataStartUtc = datetime.min  # load all you can get

        for symbol_name in self.symbols_to_load:
            error, symbol = self.request_symbol(
                symbol_name,
                Dukascopy(data_rate=0),
                TradePaper(""),
            )
            if "" != error:
                print(error)
                exit()

            symbol.request_bars(Constants.SEC_PER_HOUR)
            symbol.request_bars(2 * Constants.SEC_PER_HOUR)
            symbol.request_bars(Constants.SEC_PER_MINUTE)
            symbol.request_bars(Constants.SEC_PER_DAY)

    ###################################
    def on_start(self, symbol: Symbol) -> None:
        pass

    ###################################
    def on_tick(self, symbol: Symbol) -> None:
        pass

    ###################################
    def on_stop(self) -> None:
        print("Done")


# End of file
