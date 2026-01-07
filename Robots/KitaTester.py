import numpy as np
import mmap
import time
import ctypes
import talib  # type: ignore
from talib import MA_Type  # type: ignore
from datetime import datetime
import pytz
from Api.KitaApiEnums import *
from Api.KitaApi import KitaApi, Symbol
from Api.CoFu import *
from Api.Constants import *
from BrokerProvider.QuoteCtraderCache import QuoteCtraderCache
from BrokerProvider.TradePaper import TradePaper
import Robots.KitaTesterProto_pb2

# from Indicators.Indicators import Indicators


class KitaTester(KitaApi):

    # History
    # region
    version: str = "Template V1.0"
    # V1.0     06.12.24    HMz created
    # endregion

    # Parameter
    # region
    # These parameters can be set by the startup module like MainConsole.py
    # If not set from there, the given default values will be used
    Direction = TradeDirection.Mode1
    # endregion

    # Members
    # region
    # Named semaphore names
    # Constants
    MEMORY_MAP_NAME = "TaskMemoryMap"
    QUOTE_READY_SEMAPHORE_NAME = "QuoteReady2PySemaphore"
    QUOTE_ACC_SEMAPHORE_NAME = "QuoteAccFromPySemaphore"
    # RESULT_READY_SEMAPHORE_NAME = "ResultReady2PySemaphore"

    kernel32: ctypes.WinDLL
    memory_map: mmap.mmap
    quote_ready_semaphore = None
    quote_acc_semaphore = None
    performance_prev_time: float = 0
    is_first_run: bool = True

    def __init__(self):
        super().__init__()  # Importatnt, do not delete

    # endregion

    ###################################
    def on_init(self) -> None:
        # 1. Define quote_provider(s)
        # data_rate is in seconds, 0 means fastetst possible (i.e. Ticks)
        quote_provider = QuoteCtraderCache(
            data_rate=0,
            parameter=r"$(USERPROFILE)\AppData\Roaming\Spotware\Cache\pepperstone\BacktestingCache\V1\live_ad845a9a",
        )
        # quote_provider = BrokerMt5( data_rate=0, "62060378, pepperstone_uk-Demo, tFue0y*akr")
        # quote_provider = QuoteCsv(data_rate=0, "G:\\Meine Ablage")

        # 2. Define symbol(s); at least one symbol must be defined
        error, symbol = self.request_symbol(
            "NZDCAD",
            quote_provider,
            TradePaper(""),  # Paper trading
            # If :Normalized is added to America/New_York, 7 hours are added
            # This gives New York 17:00 = midnight so that forex trading runs from Moday 00:00 - Friday 23:59:59
            # (we call this "New York normalized time")
            # "America/New_York:Normalized",
        )
        assert "" == error

        # 4. Define one or more bars (optional)
        self.indi_period = 5
        symbol.request_bars(Constants.SEC_PER_HOUR, 2)
        symbol.request_bars(2 * Constants.SEC_PER_HOUR, self.indi_period)
        symbol.request_bars(Constants.SEC_PER_MINUTE, 2)
        symbol.request_bars(Constants.SEC_PER_DAY, 2)

        # Load kernel32.dll for semaphore operations
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        # Open memory-mapped file
        self.memory_map = mmap.mmap(-1, 1024, tagname=self.MEMORY_MAP_NAME)

        # 5. Define kita indicators (optional)
        # error, self.sma = Indicators.moving_average(
        #     source=self.m1_bars.open_bids,
        #     periods=self.indi_period,
        #     ma_type=MovingAverageType.Simple,
        # )
        # if "" != error:
        #     print(error)
        #     exit()

    ###################################
    def on_start(self, symbol: Symbol) -> None:
        # Open named semaphores
        self.quote_ready_semaphore = self.kernel32.OpenSemaphoreW(  # type:ignore
            0x1F0003, False, self.QUOTE_READY_SEMAPHORE_NAME
        )
        assert self.quote_ready_semaphore, "quote_ready_semaphore not found"

        self.quote_acc_semaphore = self.kernel32.OpenSemaphoreW(  # type:ignore
            0x1F0003, False, self.QUOTE_ACC_SEMAPHORE_NAME
        )
        assert self.quote_acc_semaphore, "quote_acc_semaphore not found"

        (error, self.hour_bars) = symbol.get_bars(Constants.SEC_PER_HOUR)
        assert "" == error
        (error, self.hour2_bars) = symbol.get_bars(2 * Constants.SEC_PER_HOUR)
        assert "" == error
        (error, self.minute_bars) = symbol.get_bars(Constants.SEC_PER_MINUTE)
        assert "" == error
        (error, self.day_bars) = symbol.get_bars(Constants.SEC_PER_DAY)
        assert "" == error
        self.performance_prev_time = time.perf_counter()

        # ta-lib indicators must be defined in on_start becaus full bars are built after on_init
        ta_funcs = talib.get_functions()  # type:ignore
        # print(ta_funcs)  # type:ignore

        np_open = np.array(self.hour2_bars.open_bids.data)
        self.ta_sma = talib.SMA(np_open, self.indi_period)
        self.upper, self.middle, self.lower = talib.BBANDS(np_open, self.indi_period, 2, 2, MA_Type.SMA)

        # Create all KitaTrader indicators for comparison
        # These use the official KitaTrader API indicators from Indicators directory
        self.kita_sma = self.Indicators.simple_moving_average(self.hour2_bars.open_bids, self.indi_period)
        self.kita_ema = self.Indicators.exponential_moving_average(self.hour2_bars.open_bids, self.indi_period)
        self.kita_wma = self.Indicators.weighted_moving_average(self.hour2_bars.open_bids, self.indi_period)
        self.kita_hma = self.Indicators.hull_moving_average(self.hour2_bars.open_bids, self.indi_period)
        self.kita_sd = self.Indicators.standard_deviation(self.hour2_bars.open_bids, self.indi_period)
        err, self.kita_bb = self.Indicators.bollinger_bands(self.hour2_bars.open_bids, self.indi_period, 2.0, MovingAverageType.Simple)
        self.kita_rsi = self.Indicators.relative_strength_index(self.hour2_bars.open_bids, self.indi_period)
        self.kita_macd = self.Indicators.macd(self.hour2_bars.open_bids, 12, 26, 9)

        pass

    ###################################
    def on_tick(self, symbol: Symbol):
        # print the time of the first tick of a new day
        # and the milliseconds it took to process the previous day
        if symbol.time.date() != symbol.prev_time.date():
            diff = (time.perf_counter() - self.performance_prev_time) * 1e3
            print(
                symbol.time.strftime("%Y-%m-%d %H:%M:%S"),
                ", ",
                symbol.time.strftime("%A"),
                ", ",
                f"{diff:.1f}",
            )
            self.performance_prev_time = time.perf_counter()

        if symbol.is_warm_up:
            return

        
        if self.is_first_run:
            self.is_first_run = False
            return

        # Step 1: Wait for QuoteMessage
        
        self.kernel32.WaitForSingleObject(self.quote_ready_semaphore, 0xFFFFFFFF)  # type:ignore

        # Read the size of the serialized message
        self.memory_map.seek(0)
        size_data = self.memory_map.read(4)  # Read the first 4 bytes
        message_size = int.from_bytes(size_data, byteorder="little")  # Convert to integer

        # Read the serialized message
        quote_message = Robots.KitaTesterProto_pb2.QuoteMessage()  # type: ignore

        try:
            quote_message.ParseFromString(self.memory_map.read(message_size))  # type: ignore
        except Exception as e:
            print(f"Error parsing QuoteMessage: {e}")
            print(f"Raw data: {serialized_data}")  # type: ignore
            raise

        if -1 == quote_message.timestamp:  # type: ignore
            print("Received exit signal from C#")
            self.stop()
            return

        # Convert quote_message.timestamp from milliseconds to seconds and ensure it's in UTC
        message_time = datetime.fromtimestamp(quote_message.timestamp / 1000, tz=pytz.UTC)  # type: ignore

        # Compare timestamps
        if int(quote_message.timestamp / 1000) != int(symbol.time.timestamp()):  # type: ignore
            print(message_time, symbol.time)
            print(f"Timestamp mismatch: {quote_message.timestamp / 1000} != {symbol.time.timestamp()}")  # type: ignore

        if quote_message.bid != symbol.bid:  # type: ignore
            print(f"Bid mismatch: {quote_message.bid} != {symbol.bid}")  # type: ignore

        if quote_message.ask != symbol.ask:  # type: ignore
            print(f"Ask mismatch: {quote_message.ask} != {symbol.ask}")  # type: ignore

        if quote_message.minute1Open != self.minute_bars.open_bids.last(1):  # type: ignore
            print(f"Minute1Open mismatch: {quote_message.minute1Open} != {self.minute_bars.open_bids.last(1)}")  # type: ignore

        if quote_message.hour1Open != self.hour_bars.open_bids.last(1):  # type: ignore
            print(f"Hour1Open mismatch: {quote_message.hour1Open} != {self.hour_bars.open_bids.last(1)}")  # type: ignore

        if quote_message.hour2Open != self.hour2_bars.open_bids.last(1):  # type: ignore
            print(f"Hour2Open mismatch: {quote_message.hour2Open} != {self.hour2_bars.open_bids.last(1)}")  # type: ignore

        if quote_message.day1Open != self.day_bars.open_bids.last(1):  # type: ignore
            print(f"DayOpen mismatch: {quote_message.day1Open} != {self.day_bars.open_bids.last(1)}")  # type: ignore

        if quote_message.hour1Close != self.hour_bars.close_bids.last(1):  # type: ignore
            print(f"Hour1Close mismatch: {quote_message.hour1Close} != {self.hour_bars.close_bids.last(1)}")  # type: ignore

        if quote_message.hour2Close != self.hour2_bars.close_bids.last(1):  # type: ignore
            print(f"Hour2Close mismatch: {quote_message.hour2Close} != {self.hour2_bars.close_bids.last(1)}")  # type: ignore

        message_time = datetime.fromtimestamp(quote_message.day1Timestamp / 1000, tz=pytz.UTC)  # type: ignore
        if int(quote_message.day1Timestamp / 1000) != int(self.day_bars.open_times.last(1).timestamp()):  # type: ignore
            print(message_time, symbol.time)
            print(f"Timestamp mismatch: {quote_message.timestamp / 1000} != {symbol.time.timestamp()}")  # type: ignore

        # Get absolute index for indicator access (for closed bar, 2 bars ago from current)
        # Use source DataSeries _add_count which tracks total bars added
        abs_index = self.hour2_bars.open_bids._add_count - 2 if self.hour2_bars.open_bids._add_count >= 2 else -1
        
        if abs_index < 0:
            return  # Not enough bars for indicator comparison
        
        # Compare SMA (talib vs C#)
        py_sma = round(self.ta_sma[self.hour2_bars.read_index-2], symbol.digits)
        cs_sma = round(quote_message.sma1, symbol.digits)
        if py_sma != cs_sma:
            print(f"SMA (talib) mismatch: {py_sma} != {cs_sma}")
        
        # Compare SMA (KitaTrader vs C#)
        try:
            kita_sma_val = self.kita_sma.result[abs_index]
            if not np.isnan(kita_sma_val):
                kita_sma_rounded = round(kita_sma_val, symbol.digits)
                if kita_sma_rounded != cs_sma:
                    print(f"SMA (KitaTrader) mismatch: {kita_sma_rounded} != {cs_sma}")
        except:
            pass

        # Compare Bollinger Bands (talib vs C#)
        py_bb_hi = round(self.upper[self.hour2_bars.read_index - 2], symbol.digits)
        cs_bb_hi = round(quote_message.bb1hi, symbol.digits)
        if py_bb_hi != cs_bb_hi:
            print(f"BB_HI (talib) mismatch: {py_bb_hi} != {cs_bb_hi}")

        py_bb_main = round(self.middle[self.hour2_bars.read_index - 2], symbol.digits)
        cs_bb_main = round(quote_message.bb1main, symbol.digits)
        if py_bb_main != cs_bb_main:
            print(f"BB_MAIN (talib) mismatch: {py_bb_main} != {cs_bb_main}")

        py_bb_lo = round(self.lower[self.hour2_bars.read_index - 2], symbol.digits)
        cs_bb_lo = round(quote_message.bb1lo, symbol.digits)
        if py_bb_lo != cs_bb_lo:
            print(f"BB_LO (talib) mismatch: {py_bb_lo} != {cs_bb_lo}")
        
        # Compare Bollinger Bands (KitaTrader vs C#)
        try:
            kita_bb_top = self.kita_bb.top[abs_index]
            kita_bb_main = self.kita_bb.main[abs_index]
            kita_bb_bottom = self.kita_bb.bottom[abs_index]
            
            if not np.isnan(kita_bb_top):
                kita_bb_top_rounded = round(kita_bb_top, symbol.digits)
                if kita_bb_top_rounded != cs_bb_hi:
                    print(f"BB_TOP (KitaTrader) mismatch: {kita_bb_top_rounded} != {cs_bb_hi}")
            
            if not np.isnan(kita_bb_main):
                kita_bb_main_rounded = round(kita_bb_main, symbol.digits)
                if kita_bb_main_rounded != cs_bb_main:
                    print(f"BB_MAIN (KitaTrader) mismatch: {kita_bb_main_rounded} != {cs_bb_main}")
            
            if not np.isnan(kita_bb_bottom):
                kita_bb_bottom_rounded = round(kita_bb_bottom, symbol.digits)
                if kita_bb_bottom_rounded != cs_bb_lo:
                    print(f"BB_BOTTOM (KitaTrader) mismatch: {kita_bb_bottom_rounded} != {cs_bb_lo}")
        except:
            pass
        
        # Compare other indicators (KitaTrader indicators - no C# reference in protobuf, but log for verification)
        try:
            kita_ema_val = self.kita_ema.result[abs_index]
            if not np.isnan(kita_ema_val):
                print(f"EMA (KitaTrader): {round(kita_ema_val, symbol.digits)}")
        except:
            pass
        
        try:
            kita_wma_val = self.kita_wma.result[abs_index]
            if not np.isnan(kita_wma_val):
                print(f"WMA (KitaTrader): {round(kita_wma_val, symbol.digits)}")
        except:
            pass
        
        try:
            kita_hma_val = self.kita_hma.result[abs_index]
            if not np.isnan(kita_hma_val):
                print(f"HMA (KitaTrader): {round(kita_hma_val, symbol.digits)}")
        except:
            pass
        
        try:
            kita_sd_val = self.kita_sd.result[abs_index]
            if not np.isnan(kita_sd_val):
                print(f"SD (KitaTrader): {round(kita_sd_val, symbol.digits)}")
        except:
            pass
        
        try:
            kita_rsi_val = self.kita_rsi.result[abs_index]
            if not np.isnan(kita_rsi_val):
                print(f"RSI (KitaTrader): {round(kita_rsi_val, symbol.digits)}")
        except:
            pass
        
        try:
            kita_macd_val = self.kita_macd.macd[abs_index]
            kita_macd_signal = self.kita_macd.signal[abs_index]
            kita_macd_hist = self.kita_macd.histogram[abs_index]
            if not np.isnan(kita_macd_val):
                print(f"MACD (KitaTrader): MACD={round(kita_macd_val, symbol.digits)}, SIGNAL={round(kita_macd_signal, symbol.digits)}, HIST={round(kita_macd_hist, symbol.digits)}")
        except:
            pass

        # Respond with a PythonResponseMessage
        response = Robots.KitaTesterProto_pb2.PythonResponseMessage(  # type: ignore
            id=1, para1="Response to QuoteMessage", is_end=False
        )
        serialized_response = response.SerializeToString()  # type: ignore
        response_length = len(serialized_response)  # type: ignore

        # Write the length followed by the message
        self.memory_map.seek(0)
        self.memory_map.write(response_length.to_bytes(4, byteorder="little"))  # Write length as 4-byte integer
        self.memory_map.write(serialized_response)  # Write serialized message # type: ignore
        self.memory_map.flush()

        
        if not self.kernel32.ReleaseSemaphore(self.quote_acc_semaphore, 1, None):
            raise OSError("Failed to release ResultReady semaphore")

    ###################################
    def on_stop(self, symbol: Symbol):
        """
        Release resources.
        """
        if self.memory_map:
            self.memory_map.close()
        if self.quote_ready_semaphore:  # type:ignore
            self.kernel32.CloseHandle(self.quote_ready_semaphore)  # type:ignore
        if self.quote_acc_semaphore:  # type:ignore
            self.kernel32.CloseHandle(self.quote_acc_semaphore)  # type:ignore

        print("Done")


# End of file
