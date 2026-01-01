from talib import MA_Type  # type: ignore
import talib
import numpy as np
from Api.KitaApiEnums import *
from Api.KitaApi import KitaApi
from Api.CoFu import *
from Api.Constants import *
from Api.Symbol import Symbol
from BrokerProvider.TradePaper import TradePaper
from BrokerProvider.QuoteDukascopy import Dukascopy
from BrokerProvider.QuoteQuantConnect import QuoteQuantConnect
import json
import os


class Ultron(KitaApi):
    # History
    # region
    version: str = "Ultron V0.11 (CFD Trading)"
    # V0.11    12.10.25    HMz - Ported from BTGymProject, tick-based TP/SL
    # V1.0     05.01.24    HMz - Created
    # endregion

    # CFD Contract Specifications
    # region
    TICK_SIZE = 0.00001    # 1 tick = 0.00001 (minimum price movement)
    TICK_VALUE = 1.0       # $1 per tick per lot
    # endregion

    # Parameters (loaded from optimizer_config.json if available)
    # region
    # These parameters can be set by the startup module like MainConsole.py
    # If not set from there, the given default values will be used
    period1 = 10
    period2 = 20
    period3 = 50
    period4 = 100
    ma1_ma2_min_val = 0.00005
    ma1_ma2_max_val = 0.00025
    ma3_ma4_diff_max_val = 0.00025
    take_profit_ticks = 1000  # 1000 ticks (100 pips equivalent)
    stop_loss_ticks = 500     # 500 ticks (50 pips equivalent)
    volume = 1                # 1 lot
    trade_direction = "Long"  # "Long", "Short", or "Both"
    data_source = "Dukascopy"  # "Dukascopy" or "QuantConnect"
    symbol_name = "EURUSD"     # Symbol to trade
    # endregion

    # Members
    # region
    def __init__(self):
        super().__init__()  # Important, do not delete
        self.trade_count = 0
        self.load_config()
    # endregion

    ###################################
    def load_config(self):
        """Load parameters from optimizer_config.json if available"""
        config_file = os.path.join(os.path.dirname(__file__), '..', 'optimizer_config.json')
        print(f"\nLooking for config file: {config_file}")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    params = config.get('default_strategy_params', {})
                    
                    # Load parameters
                    self.period1 = params.get('period1', self.period1)
                    self.period2 = params.get('period2', self.period2)
                    self.period3 = params.get('period3', self.period3)
                    self.period4 = params.get('period4', self.period4)
                    self.ma1_ma2_min_val = params.get('ma1_ma2_min_val', self.ma1_ma2_min_val)
                    self.ma1_ma2_max_val = params.get('ma1_ma2_max_val', self.ma1_ma2_max_val)
                    self.ma3_ma4_diff_max_val = params.get('ma3_ma4_diff_max_val', self.ma3_ma4_diff_max_val)
                    self.take_profit_ticks = params.get('take_profit_ticks', self.take_profit_ticks)
                    self.stop_loss_ticks = params.get('stop_loss_ticks', self.stop_loss_ticks)
                    self.volume = params.get('volume', self.volume)
                    self.trade_direction = params.get('trade_direction', self.trade_direction)
                    self.data_source = params.get('data_source', self.data_source)
                    self.symbol_name = params.get('symbol_name', self.symbol_name)
                    
                    print(f"[OK] Config loaded: data_source={self.data_source}, symbol={self.symbol_name}")
            except Exception as e:
                print(f"[WARN] Could not load config file: {e}")
        else:
            print(f"[WARN] Config file not found, using defaults")

    ###################################
    def on_init(self) -> None:
        # Select data provider based on configuration
        print(f"\n[DEBUG] on_init() called - data_source='{self.data_source}', symbol_name='{self.symbol_name}'")
        
        if self.data_source == "QuantConnect":
            # QuantConnect: Provides minute bars aggregated from second data
            quote_provider = QuoteQuantConnect(data_rate=Constants.SEC_PER_MINUTE)
            print(f"[OK] Using QuantConnect data provider (minute bars from second data)")
        else:
            quote_provider = Dukascopy(data_rate=Constants.SEC_PER_MINUTE)
            print(f"[WARN] Using Dukascopy data provider (fallback)")
        
        print(f"[DEBUG] Requesting symbol: {self.symbol_name}")
        print(f"[DEBUG] Provider: {quote_provider.provider_name}")
        print(f"[DEBUG] Data path will be: {self.DataPath}")
        
        # Request symbol to be used
        error, symbol = self.request_symbol(
            self.symbol_name,
            quote_provider,
            TradePaper(),  # Paper trading
            # If :Normalized is added to America/New_York, 7 hours are added
            # This gives New York 17:00 = midnight so that forex trading runs from Monday 00:00 - Friday 23:59:59
            # (we call this "New York normalized time")
            "America/New_York:Normalized",
        )
        if "" != error:
            print(f"[ERROR] Error requesting symbol: {error}")
            return
        
        # Request 1-minute bars
        # For QuantConnect: bars will be aggregated from tick data during backtest
        # For other providers: bars are pre-loaded from files
        lookback = max(self.period4, 200)  # Enough for largest MA
        
        # Always request bars - system will aggregate from ticks if needed
        symbol.request_bars(Constants.SEC_PER_MINUTE, lookback)
        
        if self.data_source == "QuantConnect":
            print(f"[INFO] QuantConnect: Bars will be aggregated from tick data during backtest")
        else:
            # Verify bars loaded for other providers
            error, self.mBars = symbol.get_bars(Constants.SEC_PER_MINUTE)
            if "" != error:
                print(f"[ERROR] Error getting bars: {error}")
                return
        
        print("\n" + "="*70)
        print(f"=== {self.version} ===")
        print("="*70)
        print(f"Parameters:")
        print(f"  Periods: {self.period1}/{self.period2}/{self.period3}/{self.period4}")
        print(f"  TP: {self.take_profit_ticks} ticks, SL: {self.stop_loss_ticks} ticks")
        print(f"  Direction: {self.trade_direction}")
        print(f"  Volume: {self.volume} lot(s)")
        print(f"\nCFD Specs:")
        print(f"  Tick Size: {self.TICK_SIZE} (minimum price movement)")
        print(f"  Tick Value: ${self.TICK_VALUE} per tick per lot")
        print("="*70 + "\n")

    ###################################
    def on_start(self, symbol: Symbol) -> None:
        # Members to be re-initialized on each new start
        self.trade_count = 0
        
        # Get minute bars for indicators (will be aggregated from ticks by KitaApi)
        error, minute_bars = symbol.get_bars(Constants.SEC_PER_MINUTE)
        if error != "":
            print(f"[WARN] Could not get minute bars: {error}")
            print(f"[INFO] Indicators will be calculated from tick data")
        
        # Moving Averages using talib (KitaTrader style)
        # talib indicators will be calculated on each tick from aggregated bars
        print(f"[INFO] Indicators ready: WMA({self.period1},{self.period2}), SMA({self.period3},{self.period4})")

    ###################################
    def on_tick(self, symbol: Symbol):
        # Skip if not enough data for indicators
        if symbol.is_warm_up:
            return
        
        # Get minute bars (aggregated from ticks by KitaApi)
        error, minute_bars = symbol.get_bars(Constants.SEC_PER_MINUTE)
        if error != "" or minute_bars is None or minute_bars.count < max(self.period4, 2):
            return  # Not enough data yet
        
        # Calculate moving averages using talib
        # Get close prices as numpy array
        close_bids = np.array(minute_bars.close_bids.data[:minute_bars.count])
        close_asks = np.array(minute_bars.close_asks.data[:minute_bars.count])
        
        # Calculate MAs (WMA and SMA)
        ma1_array = talib.WMA(close_bids, timeperiod=self.period1)
        ma2_array = talib.WMA(close_bids, timeperiod=self.period2)
        ma3_array = talib.SMA(close_bids, timeperiod=self.period3)
        ma4_array = talib.SMA(close_bids, timeperiod=self.period4)
        
        # Get current MA values (last non-NaN value)
        ma1_value = ma1_array[-1] if not np.isnan(ma1_array[-1]) else 0
        ma2_value = ma2_array[-1] if not np.isnan(ma2_array[-1]) else 0
        ma3_value = ma3_array[-1] if not np.isnan(ma3_array[-1]) else 0
        ma4_value = ma4_array[-1] if not np.isnan(ma4_array[-1]) else 0
        
        # Skip if any MA is not ready (NaN)
        if any(np.isnan([ma1_value, ma2_value, ma3_value, ma4_value])):
            return
        
        # Calculate MA differences
        ma1_ma2 = abs(ma1_value - ma2_value)
        ma2_ma1 = abs(ma2_value - ma1_value)
        ma3_ma4_diff = abs(ma3_value - ma4_value)
        
        # Get current and previous bar data for entry conditions
        # Note: minute_bars is already retrieved above for MA calculations
        
        # Check TP/SL for open positions
        if len(self.positions) > 0:
            for pos in self.positions:
                ticks_profit = (pos.current_price - pos.entry_price) / self.TICK_SIZE
                if pos.trade_type == TradeType.Sell:
                    ticks_profit = -ticks_profit
                
                # Close on TP or SL
                if ticks_profit >= self.take_profit_ticks or ticks_profit <= -self.stop_loss_ticks:
                    exit_type = "TP" if ticks_profit > 0 else "SL"
                    pnl = ticks_profit * self.TICK_VALUE * pos.volume_in_units
                    
                    print(f"{symbol.time.strftime('%Y-%m-%d %H:%M:%S')} - "
                          f"{exit_type}: Closed position - ${pnl:.2f} ({ticks_profit:.1f} ticks)")
                    
                    symbol.trade_provider.close_position(pos)
                    break
        
        # Entry logic (only if no position)
        if len(self.positions) == 0:
            # Check MA3/MA4 diff filter
            if ma3_ma4_diff < self.ma3_ma4_diff_max_val:
                
                # Check if we have enough bar data for entry conditions (need at least 2 bars)
                has_bar_data = minute_bars.count >= 2
                
                # SHORT Entry
                if self.trade_direction in ["Short", "Both"] and has_bar_data:
                    # Check bar patterns: current bar close < previous close, previous close < previous open
                    bar_condition = (minute_bars[0].Bid.Close < minute_bars[1].Bid.Close and
                                    minute_bars[1].Bid.Close < minute_bars[1].Bid.Open)
                    
                    if (ma3_value > ma1_value and
                        ma3_value > ma2_value and
                        bar_condition and
                        self.ma1_ma2_min_val < ma1_ma2 < self.ma1_ma2_max_val):
                        
                        self.place_order(TradeType.Sell, symbol)
                
                # LONG Entry
                if self.trade_direction in ["Long", "Both"] and has_bar_data:
                    # Check bar patterns: current bar close > previous close, previous close > previous open
                    bar_condition = (minute_bars[0].Ask.Close > minute_bars[1].Ask.Close and
                                    minute_bars[1].Ask.Close > minute_bars[1].Ask.Open)
                    
                    if (ma3_value < ma1_value and
                        ma3_value < ma2_value and
                        bar_condition and
                        self.ma1_ma2_min_val < ma2_ma1 < self.ma1_ma2_max_val):
                        
                        self.place_order(TradeType.Buy, symbol)

    ###################################
    def place_order(self, trade_type: TradeType, symbol: Symbol):
        """
        Place market order with automatic TP/SL management
        Note: KitaTrader handles TP/SL via manual checking in on_tick (as shown above)
        """
        # Execute market order
        pos = symbol.trade_provider.execute_market_order(
            trade_type,
            symbol.name,
            symbol.normalize_volume_in_units(self.volume),
            self.get_label(symbol)
        )
        
        if pos:
            self.trade_count += 1
            entry_price = pos.entry_price
            direction = "LONG" if trade_type == TradeType.Buy else "SHORT"
            
            print(f"{symbol.time.strftime('%Y-%m-%d %H:%M:%S')} - "
                  f"{direction} Entry #{self.trade_count}: {self.volume} lots at {entry_price:.5f} "
                  f"({'ASK' if trade_type == TradeType.Buy else 'BID'})")
        
        return pos

    ###################################
    def get_label(self, symbol: Symbol):
        """Generate trade label"""
        return (
            f"{self.version};"
            f"{self.trade_count};"
            f"{symbol.time};"
        )

    ###################################
    def on_stop(self, symbol: Symbol):
        """Called when backtest ends"""
        print("\n" + "="*70)
        print("BACKTEST RESULTS")
        print("="*70)
        print(f"Starting Value: ${self.AccountInitialBalance:,.2f}")
        print(f"Final Value:    ${self.account.balance:,.2f}")
        pnl = self.account.balance - self.AccountInitialBalance
        pnl_pct = (pnl / self.AccountInitialBalance) * 100
        print(f"P&L:            ${pnl:,.2f} ({pnl_pct:+.2f}%)")
        print(f"\nTotal Trades:   {len(self.history)}")
        print(f"Max Drawdown:   ${self.max_equity_drawdown_value:,.2f}")
        
        winning_trades = len([x for x in self.history if x.net_profit >= 0])
        losing_trades = len([x for x in self.history if x.net_profit < 0])
        win_rate = (winning_trades / len(self.history) * 100) if len(self.history) > 0 else 0
        
        print(f"Win Rate:       {win_rate:.1f}% ({winning_trades} wins / {losing_trades} losses)")
        print("="*70)
