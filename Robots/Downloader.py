from KitaApiEnums import *
from KitaApi import KitaApi, Symbol
from Api.CoFu import *
from Constants import *
from TradePaper import TradePaper
from QuoteMe import QuoteMe  # type: ignore
from QuoteDukascopy import Dukascopy  # type: ignore
from QuoteTradeMt5 import BrokerMt5  # type: ignore
from QuoteCsv import QuoteCsv  # type: ignore


class Downloader(KitaApi):

    # History
    # region
    version: str = "Downloader V1.0"
    # V1.0     03.01.25     HMz created
    # endregion

    # Members
    # region
    symbols_to_load: list[str] = [
        "GBP_USD",
        # "EUR_USD",
        # "NZD_CAD",
        # "AUD_CAD",
        # "DEU.IDX_EUR",
        # "USA30.IDX_USD",
        # "USATECH.IDX_USD",
        # "USA500.IDX_USD",
        # "XAU_USD",
    ]

    def __init__(self):
        super().__init__()  # Importatnt, do not delete

    # endregion

    ###################################
    def on_init(self) -> None:
        self.robot.AllDataStartUtc = datetime.min  # load all you can get
        # self.robot.AllDataStartUtc = datetime.strptime("1.1.2014", "%d.%m.%Y")

        # Define quote_provider(s)
        # datarate is in seconds, 0 means fastetst possible (i.e. Ticks)
        quote_provider = Dukascopy("", datarate=Constants.SEC_PER_MINUTE)
        # quote_provider = QuoteMe("G:\\Meine Ablage\\TickBars", datarate=0),
        # quote_provider = BrokerMt5("62060378, pepperstone_uk-Demo, tFue0y*akr", datarate=0)
        # quote_provider = QuoteCsv("G:\\Meine Ablage", datarate=0)

        for symbol_name in self.symbols_to_load:
            error, symbol = self.request_symbol(
                symbol_name,
                quote_provider,
                TradePaper(""),
            )
            if "" != error:
                print(error)
                exit()

            # Define one or more bars (optional)
            error, self.h4_bars = symbol.request_bars(4 * Constants.SEC_PER_HOUR)
            error, self.d3_bars = symbol.request_bars(3 * Constants.SEC_PER_DAY)
            error, self.d1_bars = symbol.request_bars(Constants.SEC_PER_DAY)
            error, self.m5_bars = symbol.request_bars(5 * Constants.SEC_PER_MINUTE)
            error, self.m1_bars = symbol.request_bars(Constants.SEC_PER_MINUTE)
            error, self.h1_bars = symbol.request_bars(Constants.SEC_PER_HOUR)

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
