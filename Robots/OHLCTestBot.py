"""
OHLC Test Bot - 1:1 lock step port from C# OHLCTestBot
Logs bars with SMA indicators - matches C# bot logic exactly
"""
import os
import math
from datetime import datetime
from Api.KitaApi import KitaApi
from Api.Symbol import Symbol
from Api.BarOpenedEventArgs import BarOpenedEventArgs


class OHLCTestBot(KitaApi):
    """Test bot to log all OHLCV values with SMA for comparison with C# - 1:1 port"""
    
    def __init__(self):
        super().__init__()
        self.symbol_name = "AUDNZD"
        
        # Bars for different timeframes
        self.m_bars_m1 = None
        self.m_bars_m5 = None
        self.m_bars_h1 = None
        self.m_bars_h4 = None
        
        # SMAs
        self.m_sma_m1_open = None
        self.m_sma_m1_high = None
        self.m_sma_m1_low = None
        self.m_sma_m1_close = None
        
        self.m_sma_m5_open = None
        self.m_sma_m5_high = None
        self.m_sma_m5_low = None
        self.m_sma_m5_close = None
        
        self.m_sma_h1_open = None
        self.m_sma_h1_high = None
        self.m_sma_h1_low = None
        self.m_sma_h1_close = None
        
        self.m_sma_h4_open = None
        self.m_sma_h4_high = None
        self.m_sma_h4_low = None
        self.m_sma_h4_close = None
        
        self.m_sma_periods = 23
        self.log_file = None
    
    def on_init(self) -> None:
        log_dir = r"C:\Users\HMz\Documents\cAlgo\Logfiles"
        if not os.path.exists(log_dir): os.makedirs(log_dir)
        log_path = os.path.join(log_dir, "OHLCTestBot_Python.log")
        self.log_file = open(log_path, "w", encoding="utf-8")
        
        err, self.active_symbol = self.request_symbol(self.symbol_name, self.quote_provider, self.trade_provider)
        if self.active_symbol:
            self.active_symbol.request_bars(60, 2000)
            self.active_symbol.request_bars(300, 500)
            self.active_symbol.request_bars(3600, 100)
            self.active_symbol.request_bars(14400, 50)
    
    def on_start(self, symbol: Symbol) -> None:
        self.m_bars_m1 = self.MarketData.GetBars(60, self.symbol_name)
        self.m_bars_m5 = self.MarketData.GetBars(300, self.symbol_name)
        self.m_bars_h1 = self.MarketData.GetBars(3600, self.symbol_name)
        self.m_bars_h4 = self.MarketData.GetBars(14400, self.symbol_name)
        
        if self.m_bars_m1 is None or self.m_bars_m5 is None or self.m_bars_h1 is None or self.m_bars_h4 is None:
            return
        
        self._log(f"OHLCTestBot started: Symbol={self.symbol_name}")
        
        # Helper to create SMAs for a timeframe
        def create_t_smas(bars):
            return (
                self.Indicators.simple_moving_average(bars.OpenPrices, self.m_sma_periods),
                self.Indicators.simple_moving_average(bars.HighPrices, self.m_sma_periods),
                self.Indicators.simple_moving_average(bars.LowPrices, self.m_sma_periods),
                self.Indicators.simple_moving_average(bars.ClosePrices, self.m_sma_periods)
            )

        self.m_sma_m1_open, self.m_sma_m1_high, self.m_sma_m1_low, self.m_sma_m1_close = create_t_smas(self.m_bars_m1)
        self.m_sma_m5_open, self.m_sma_m5_high, self.m_sma_m5_low, self.m_sma_m5_close = create_t_smas(self.m_bars_m5)
        self.m_sma_h1_open, self.m_sma_h1_high, self.m_sma_h1_low, self.m_sma_h1_close = create_t_smas(self.m_bars_h1)
        self.m_sma_h4_open, self.m_sma_h4_high, self.m_sma_h4_low, self.m_sma_h4_close = create_t_smas(self.m_bars_h4)
        
        self.m_bars_m1.BarOpened += lambda args: self.on_bar_opened("M1", args)
        self.m_bars_m5.BarOpened += lambda args: self.on_bar_opened("M5", args)
        self.m_bars_h1.BarOpened += lambda args: self.on_bar_opened("H1", args)
        self.m_bars_h4.BarOpened += lambda args: self.on_bar_opened("H4", args)
        self._log("Subscribed to BarOpened events.")
    
    def on_tick(self, symbol: Symbol):
        time_str = symbol.time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] if symbol.time else ""
        fmt = ".20f"
        self._log(f"{time_str},{symbol.bid:{fmt}},{symbol.ask:{fmt}},{symbol.spread:{fmt}}")
    
    def on_stop(self, symbol: Symbol = None):
        if self.log_file:
            self.log_file.close()
            self.log_file = None
    
    def on_bar_opened(self, tf: str, args: BarOpenedEventArgs):
        if args.Bars.count < 2: return
        bar = args.Bars.Last(1)
        if bar is None: return
        
        # Absolute index of the CLOSED bar
        index = args.Bars._bar_buffer._add_count - 2
        fmt = ".20f"
        
        sma_o, sma_h, sma_l, sma_c = None, None, None, None
        if tf == "M1": 
            sma_o, sma_h, sma_l, sma_c = self.m_sma_m1_open, self.m_sma_m1_high, self.m_sma_m1_low, self.m_sma_m1_close
        elif tf == "M5": 
            sma_o, sma_h, sma_l, sma_c = self.m_sma_m5_open, self.m_sma_m5_high, self.m_sma_m5_low, self.m_sma_m5_close
        elif tf == "H1": 
            sma_o, sma_h, sma_l, sma_c = self.m_sma_h1_open, self.m_sma_h1_high, self.m_sma_h1_low, self.m_sma_h1_close
        elif tf == "H4": 
            sma_o, sma_h, sma_l, sma_c = self.m_sma_h4_open, self.m_sma_h4_high, self.m_sma_h4_low, self.m_sma_h4_close
        
        def get_val(sma):
            if sma and index >= (self.m_sma_periods - 1):
                try:
                    val = sma.result[index]
                    if not math.isnan(val): return f"{val:{fmt}}"
                except: pass
            return ""

        sO, sH, sL, sC = get_val(sma_o), get_val(sma_h), get_val(sma_l), get_val(sma_c)
        bar_time = bar.OpenTime.strftime("%Y-%m-%d %H:%M:%S")
        self._log(f"FINAL_BAR|{tf}|{bar_time}|{bar.Open:{fmt}}|{bar.High:{fmt}}|{bar.Low:{fmt}}|{bar.Close:{fmt}}|{bar.TickVolume}|{sO}|{sH}|{sL}|{sC}")
    
    def _log(self, message: str):
        if self.log_file:
            timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S.%f")[:-3]
            self.log_file.write(f"{timestamp} | Info | {message}\n")
            self.log_file.flush()
