import os
import pandas as pd
import AlgoApi
from Settings import BinSettings
from QuoteBar import QuoteBar
from SymbolInfo import SymbolInfo
from AlgoApi import AlgoApi


######################################
class ProviderQuote:
    def __init__(self, algo_api: AlgoApi, symbol_info: SymbolInfo):
        self.bin_settings: BinSettings = algo_api.bin_settings
        self.symbol_info: SymbolInfo = symbol_info

    ######################################
    def __del__(self):
        del self.df_start

    ######################################
    def get_quote_bar_at_date(self, dt) -> tuple[str, QuoteBar]:
        filename = self.bars_filename = os.path.join(
            self.bin_settings.platform_parameter,
            self.symbol_info.name,
            self.symbol_info.name + ".csv",
        )

        # Read the CSV file without header and with specified column names
        df = pd.read_csv(
            filename,
            names=["Date", "Time", "Open", "High", "Low", "Close", "Volume"],
            header=None,
            dtype={
                "Open": float,
                "High": float,
                "Low": float,
                "Close": float,
                "Volume": int,
            },
        )

        # Combine and convert date and time columns to a single datetime column
        df["date_time"] = pd.to_datetime(
            df["Date"] + " " + df["Time"], utc=True, format="%Y.%m.%d %H:%M"
        )

        # Drop the original date and time columns
        df.drop(["Date", "Time"], axis=1, inplace=True)

        # Filter the data_frame to include only entries starting from the given date
        self.df_start = df[df["date_time"] >= pd.Timestamp(self.bin_settings.start_dt)]

        # Delete the data_frame
        del df

        self.current_index = 0
        error, quote = self.read_quote_bar()

        return error, quote

    ######################################
    def get_next_quote_bar(self) -> tuple[str, QuoteBar]:
        error, quote = self.read_quote_bar()
        return error, quote

    ######################################
    def read_quote_bar(self) -> tuple[str, QuoteBar]:
        quote = None
        error = "No more data"
        if self.current_index < len(self.df_start):
            quote = QuoteBar()
            quote.time = self.df_start.iloc[self.current_index].date_time
            quote.open = self.df_start.iloc[self.current_index].open
            quote.high = self.df_start.iloc[self.current_index].High
            quote.low = self.df_start.iloc[self.current_index].Low
            quote.close = self.df_start.iloc[self.current_index].close
            quote.volume = self.df_start.iloc[self.current_index].Volume
            quote.open_ask = quote.open + 12 * 1e-5  # set spread to 12 toints
            self.current_index += 1
            error = ""

        return error, quote


# end of file
