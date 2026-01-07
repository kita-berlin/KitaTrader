"""
OHLC Test Bot - Logs bars only (M1, M5, H1, H4)
"""
import os
from datetime import datetime
from Api.KitaApi import KitaApi
from Api.Symbol import Symbol
from Api.BarOpenedEventArgs import BarOpenedEventArgs
from Api.KitaApiEnums import MovingAverageType


class OHLCTestBot(KitaApi):
    """Test bot to log all OHLCV values for M1, M5, H1, H4 bars"""
    
    def __init__(self):
        super().__init__()
        self.symbol_name = "AUDNZD"
        
        # Bars for different timeframes
        self.m_bars_m1 = None
        self.m_bars_m5 = None
        self.m_bars_h1 = None
        self.m_bars_h4 = None
        
        # Indicator period
        self.m_periods = 20
        
        # Dictionary to store all indicators for each timeframe
        self.m_inds = {}
        
        self.log_file = None
        self.debug_log_file = None
    
    def on_init(self) -> None:
        log_dir = r"C:\Users\HMz\Documents\cAlgo\Logfiles"
        if not os.path.exists(log_dir): os.makedirs(log_dir)
        log_path = os.path.join(log_dir, "OHLCTestBot_Python.log")
        self.log_file = open(log_path, "w", encoding="utf-8")
        self.log_file.write(f"=== FRESH RUN STARTED AT {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        self.log_file.flush()
        
        # Debug log file
        debug_log_path = os.path.join(log_dir, "OHLCTestBot_Debug.log")
        self.debug_log_file = open(debug_log_path, "w", encoding="utf-8")
        self._debug_log("on_init() STARTED")
        
        err, self.active_symbol = self.request_symbol(self.symbol_name, self.quote_provider, self.trade_provider)
        self._debug_log(f"request_symbol() returned: err={err}, symbol={'OK' if self.active_symbol else 'None'}")
        
        if self.active_symbol:
            self._debug_log("Requesting bars for all timeframes...")
            self.active_symbol.request_bars(60, 2000)
            self._debug_log("  M1 bars requested")
            self.active_symbol.request_bars(300, 500)
            self._debug_log("  M5 bars requested")
            self.active_symbol.request_bars(3600, 100)
            self._debug_log("  H1 bars requested")
            self.active_symbol.request_bars(14400, 50)
            self._debug_log("  H4 bars requested")
        
        self._debug_log("on_init() COMPLETED")

    def on_start(self, symbol: Symbol) -> None:
        self._debug_log("on_start() STARTED")
        
        self.m_bars_m1 = self.MarketData.GetBars(60, self.symbol_name)
        self._debug_log("  Got M1 bars")
        self.m_bars_m5 = self.MarketData.GetBars(300, self.symbol_name)
        self._debug_log("  Got M5 bars")
        self.m_bars_h1 = self.MarketData.GetBars(3600, self.symbol_name)
        self._debug_log("  Got H1 bars")
        self.m_bars_h4 = self.MarketData.GetBars(14400, self.symbol_name)
        self._debug_log("  Got H4 bars")
        
        if self.m_bars_m1 is None or self.m_bars_m5 is None or self.m_bars_h1 is None or self.m_bars_h4 is None:
            self._debug_log("ERROR: Some bars are None - returning early")
            return
        
        # Create all indicators for testing
        self._debug_log("Creating all test indicators...")
        # Helper to create all indicators for a timeframe using Open prices
        def create_t_indicators(bars):
            sma = self.Indicators.simple_moving_average(bars.OpenPrices, self.m_periods)
            ema = self.Indicators.exponential_moving_average(bars.OpenPrices, self.m_periods)
            wma = self.Indicators.weighted_moving_average(bars.OpenPrices, self.m_periods)
            hma = self.Indicators.hull_moving_average(bars.OpenPrices, self.m_periods)
            sd = self.Indicators.standard_deviation(bars.OpenPrices, self.m_periods)
            err, bb = self.Indicators.bollinger_bands(bars.OpenPrices, self.m_periods, 1.4, MovingAverageType.Simple)
            rsi = self.Indicators.relative_strength_index(bars.OpenPrices, self.m_periods)
            macd = self.Indicators.macd(bars.OpenPrices, 12, 26, 9)
            indicators_dict = {
                'SMA': sma,
                'EMA': ema,
                'WMA': wma,
                'HMA': hma,
                'SD': sd,
                'BB_TOP': bb.top,
                'BB_MAIN': bb.main,
                'BB_BOTTOM': bb.bottom,
                'RSI': rsi,
                'MACD': macd.macd,
                'MACD_SIGNAL': macd.signal,
                'MACD_HIST': macd.histogram
            }
            ind_list = [sma, ema, wma, hma, sd, bb.top, rsi, macd.macd]
            return {
                'dict': indicators_dict,
                'list': ind_list
            }
        # Create indicators for all timeframes using Open prices (not Close)
        self.m_inds["M1"] = create_t_indicators(self.m_bars_m1)
        self._debug_log("  M1 indicators created")
        self.m_inds["M5"] = create_t_indicators(self.m_bars_m5)
        self._debug_log("  M5 indicators created")
        self.m_inds["H1"] = create_t_indicators(self.m_bars_h1)
        self._debug_log("  H1 indicators created")
        self.m_inds["H4"] = create_t_indicators(self.m_bars_h4)
        self._debug_log("  H4 indicators created")
        
        self._debug_log("Registering BarOpened event handlers...")
        self.m_bars_m1.BarOpened += lambda args: self.on_bar_opened("M1", args)
        self.m_bars_m5.BarOpened += lambda args: self.on_bar_opened("M5", args)
        self.m_bars_h1.BarOpened += lambda args: self.on_bar_opened("H1", args)
        self.m_bars_h4.BarOpened += lambda args: self.on_bar_opened("H4", args)
        self._debug_log("on_start() COMPLETED")
    
    def on_tick(self, symbol: Symbol):
        """
        Called on each tick - intentionally empty.
        Validation only happens on bar open events (on_bar_opened), not on ticks.
        """
        # Debug: Log first few ticks to track progress
        if not hasattr(self, '_tick_count'):
            self._tick_count = 0
        self._tick_count += 1
        
        # Log every 10000 ticks to track progress without flooding
        if self._tick_count % 10000 == 0:
            self._debug_log(f"on_tick() called {self._tick_count} times, current time: {symbol.time if hasattr(symbol, 'time') else 'N/A'}")
        pass
    
    def on_stop(self, symbol: Symbol = None):
        self._debug_log("on_stop() called")
        if self.log_file:
            self.log_file.close()
            self.log_file = None
        if self.debug_log_file:
            self.debug_log_file.close()
            self.debug_log_file = None
    
    def on_bar_opened(self, tf: str, args: BarOpenedEventArgs):
        self._debug_log(f"on_bar_opened({tf}) STARTED - count={args.Bars.count}")
        
        if args.Bars.count < 2: 
            self._debug_log(f"on_bar_opened({tf}) - count < 2, returning early")
            return
        bar = args.Bars.Last(1)
        if bar is None: 
            self._debug_log(f"on_bar_opened({tf}) - bar is None, returning early")
            return
        
        # Rounding based on symbol digits
        digits = self.active_symbol.digits if self.active_symbol else 5
        fmt = f".{digits}f"
        
        # Log bar
        bar_time = bar.OpenTime.strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"FINAL_BAR|{tf}|{bar_time}|{bar.Open:{fmt}}|{bar.High:{fmt}}|{bar.Low:{fmt}}|{bar.Close:{fmt}}|{bar.TickVolume}"
        
        # Write to log file
        if self.log_file:
            self.log_file.write(f"{log_line}\n")
            self.log_file.flush()
        
        # Print to console
        print(log_line)
        
        # Log indicator values (at last(1) = last completed bar, matching args.Bars.Last(1))
        # Access indicator values:
        # - Simple indicators (SMA, EMA, WMA, HMA, SD, RSI): use .result.last(1)
        # - Bollinger Bands (top, main, bottom): already DataSeries, use .last(1)
        # - MACD (macd, signal, histogram): already DataSeries, use .last(1)
        if tf in self.m_inds and args.Bars.count >= self.m_periods:
            inds = self.m_inds[tf]['dict']
            
            try:
                ind_line = f"FINAL_IND|{tf}|{bar_time}|" + \
                    f"SMA={inds['SMA'].result.last(1):{fmt}}|" + \
                    f"EMA={inds['EMA'].result.last(1):{fmt}}|" + \
                    f"WMA={inds['WMA'].result.last(1):{fmt}}|" + \
                    f"HMA={inds['HMA'].result.last(1):{fmt}}|" + \
                    f"SD={inds['SD'].result.last(1):{fmt}}|" + \
                    f"BB_TOP={inds['BB_TOP'].last(1):{fmt}}|" + \
                    f"BB_MAIN={inds['BB_MAIN'].last(1):{fmt}}|" + \
                    f"BB_BOTTOM={inds['BB_BOTTOM'].last(1):{fmt}}|" + \
                    f"RSI={inds['RSI'].result.last(1):{fmt}}|" + \
                    f"MACD={inds['MACD'].last(1):{fmt}}|" + \
                    f"MACD_SIGNAL={inds['MACD_SIGNAL'].last(1):{fmt}}|" + \
                    f"MACD_HIST={inds['MACD_HIST'].last(1):{fmt}}"
                
                # Write to log file
                if self.log_file:
                    self.log_file.write(f"{ind_line}\n")
                    self.log_file.flush()
                
                # Print to console
                print(ind_line)
            except Exception as e:
                self._debug_log(f"Error logging indicators for {tf}: {e}")
    
    def _log(self, message: str):
        if self.log_file:
            if message.startswith("FINAL_BAR|"):
                self.log_file.write(f"{message}\n")
            else:
                timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S.%f")[:-3]
                self.log_file.write(f"{timestamp} | Info | {message}\n")
            self.log_file.flush()
    
            except Exception as e:
                self._debug_log(f"Error logging indicators for {tf}: {e}")
