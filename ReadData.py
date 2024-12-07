import os
import struct
from datetime import datetime
import pandas as pd


class Bar:
    def __init__(self):
        self.time = None
        self.milli_seconds = 0
        self.open = 0
        self.high = 0
        self.low = 0
        self.close = 0
        self.volume = 0
        self.open_spread = 0

    def to_dict(self):
        return {
            "Time": self.time,
            "milli_seconds": self.milli_seconds,
            "Open": self.open,
            "High": self.High,
            "Low": self.Low,
            "Close": self.close,
            "Volume": self.Volume,
            "open_spread": self.open_spread,
        }


class market_file:
    def __init__(self, file_path, point_size, digits):
        self.file_handle = open(file_path, "rb")
        self.point_size = point_size
        self.digits = digits
        self.last_date_time = None

    def read_quote_bar(self):
        quote = Bar()
        dt_data = self.file_handle.read(8)
        if dt_data == b"":
            return None

        unpacked_dt = struct.unpack("<Q", dt_data)[0]
        timestamp = unpacked_dt // 1000
        self.last_date_time = quote.open_time = datetime.utcfromtimestamp(timestamp)
        quote.milli_seconds = unpacked_dt % 1000

        for attribute in ["Open", "High", "Low", "Close", "open_spread"]:
            value = struct.unpack("<L", self.file_handle.read(4))[0]
            setattr(quote, attribute, round(value * self.point_size, self.digits))

        quote.volume = struct.unpack("<L", self.file_handle.read(4))[0]
        return quote


def read_forex_data(filepath, point_size, digits):
    market_file = market_file(filepath, point_size, digits)
    data = []
    while True:
        bar = market_file.read_quote_bar()
        if bar is None:
            break
        data.append(bar.to_dict())
    return pd.DataFrame(data)


def process_directory(directory, point_size, digits):
    all_data = pd.DataFrame()
    for filename in os.listdir(directory):
        if filename.endswith(".mbars"):
            filepath = os.path.join(directory, filename)
            df = read_forex_data(filepath, point_size, digits)
            all_data = pd.concat([all_data, df], ignore_index=True)
    return all_data


# Specify the directory containing the .mbars Files
directory = "symbol_data/NZDCAD/m1"  # Update this with the actual directory path
point_size = 0.00001  # Update as per your data specifics
digits = 5  # Update as per your data specifics

# Process all Files in the directory
df = process_directory(directory, point_size, digits)
df.set_index("Time", inplace=True)
df.sort_index(inplace=True)

df.to_pickle("combined_forex_data_test.pkl")
# df_test = pd.read_pickle('combined_forex_data.pkl')
