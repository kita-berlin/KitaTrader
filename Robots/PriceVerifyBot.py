from __future__ import annotations
import os
from datetime import datetime, timedelta
from Api.KitaApiEnums import *
from Api.KitaApi import KitaApi
from Api.Symbol import Symbol
from BrokerProvider.QuoteCtraderCache import QuoteCtraderCache
from BrokerProvider.TradePaper import TradePaper
from Api.Constants import Constants
import pytz

# Custom QuoteProvider to support local tick cache (as defined in Kanga2 port)
class QuoteCtraderCacheTick(QuoteCtraderCache):
    """Custom QuoteCtraderCache that uses 'tick' instead of 't1' for cache path"""
    def init_symbol(self, api: KitaApi, symbol: Symbol):
        self.api = api
        self.symbol = symbol
        ctrader_path = api.resolve_env_variables(self.parameter)
        # Assuming format {Base}/{Symbol}/tick/
        self.cache_path = os.path.join(ctrader_path, self.symbol.name, "tick")

class PriceVerifyBot(KitaApi):
    """
    Python equivalent of PriceVerifyBot
    Logs Bid/Ask at the top of every hour.
    """
    
    # Parameters matches C# Bot
    symbol_name: str = "AUDNZD"
    
    # Internal state
    last_hour: int = -1
    log_file = None
    
    def __init__(self):
        super().__init__()
        # Set up providers locally if running standalone, 
        # but in MainConsole context they are injecting via properties usually.
        # We will configure them in do_init/on_init cycle or let MainConsole handle it.
        pass

    def on_init(self) -> None:
        """Called when bot starts"""
        # Define log path
        log_dir = r"C:\Users\HMz\Documents\cAlgo\Logfiles"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        log_path = os.path.join(log_dir, "PriceVerify_Python_Winter_D1.csv")
        self.log_file = open(log_path, "w", encoding="utf-8")
        self.log_file.write("Date,Time,Bid,Ask\n")
        self.log_file.flush()
        
        print(f"Logging to {log_path}")
        
        # Request symbol to initialize data structures
        err, self.active_symbol = self.request_symbol(self.symbol_name, self.quote_provider, self.trade_provider)
        if err == "":
            self.active_symbol.request_bars(86400)

    def on_start(self, symbol: Symbol) -> None:
        """Called when backtest starts for a specific symbol"""
        pass

    def on_tick(self, symbol: Symbol):
        """Main tick processing - checks for Daily bar completion"""
        
        # Ensure Daily Bars are available
        err, bars = symbol.get_bars(86400)
        if "" != err:
            return

        if bars.is_new_bar and bars.count > 1:
            # The PREVIOUS bar just closed (index count-2, accessed via last(1))
            
            t = bars.open_times.last(1)
            o = round(bars.open_bids.last(1), symbol.digits)
            h = round(bars.high_bids.last(1), symbol.digits)
            l = round(bars.low_bids.last(1), symbol.digits)
            c = round(bars.close_bids.last(1), symbol.digits)
            v = bars.volume_bids.last(1) + bars.volume_asks.last(1)
            
            date_str = t.strftime("%Y.%m.%d %H:%M")
            # Format: yyyy.MM.dd HH:mm,Open,High,Low,Close,Volume
            line = f"{date_str},{o:.{symbol.digits}f},{h:.{symbol.digits}f},{l:.{symbol.digits}f},{c:.{symbol.digits}f},{v:.2f}\n"
            
            if self.log_file:
                self.log_file.write(line)
                self.log_file.flush()
            
            print(f"Logged Bar: {line.strip()}")

    def on_stop(self, symbol: Symbol = None):
        if self.log_file:
            self.log_file.close()

# Integration with MainConsole
# This section allows the file to be run directly if needed, or configured in MainConsole
if __name__ == "__main__":
    # This block is for testing/running directly if we build a mini-runner here.
    # However, standard practice is to use MainConsole.py.
    # We will instruct user to use MainConsole.py with this bot.
    pass
