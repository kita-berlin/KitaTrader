"""
MarketData API - Centralized access to bars and market data
Similar to cTrader's mBot.MarketData.GetBars()
"""
from typing import Optional
from Api.Bars import Bars
from Api.Symbol import Symbol
from Api.KitaApiEnums import *
from Api.Constants import Constants


class MarketData:
    """
    Central API for accessing market data (bars, ticks).
    Similar to cTrader's mBot.MarketData.
    """
    def __init__(self, api):
        """
        Initialize the MarketData accessor.
        
        Args:
            api: KitaApi instance to access symbols
        """
        self.api = api
        self._requested_bars = []  # Track bar requests for warm-up calculation
    
    def GetBars(self, timeframe: int, symbol_name: Optional[str] = None) -> Optional[Bars]:
        """
        Get bars for the specified timeframe.
        
        Similar to cTrader's:
            mBotBars = mBot.MarketData.GetBars(TimeFrame.Hour4, symbolName);
            mM1Bars = mBot.MarketData.GetBars(TimeFrame.Minute, symbolName);
        
        Args:
            timeframe: Timeframe in seconds (e.g., Constants.SEC_PER_HOUR, Constants.SEC_PER_MINUTE)
            symbol_name: Optional symbol name. If None, uses the first symbol in symbol_dictionary.
        
        Returns:
            Bars object or None if error
        """
        # Get symbol
        if symbol_name is None:
            # Use first symbol if available
            if len(self.api.symbol_dictionary) == 0:
                return None
            symbol = list(self.api.symbol_dictionary.values())[0]
        else:
            if symbol_name not in self.api.symbol_dictionary:
                return None
            symbol = self.api.symbol_dictionary[symbol_name]
        
        # Get bars (this will return error string and Bars)
        error, bars = symbol.get_bars(timeframe)
        
        if error != "":
            
            return None
        
        # Track this bar request for warm-up calculation
        self._requested_bars.append({
            'timeframe': timeframe,
            'symbol_name': symbol.name,
            'bars': bars
        })
        
        return bars
    

