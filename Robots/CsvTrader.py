from __future__ import annotations
import csv
import os
from datetime import datetime
from typing import List, Optional
from Api.KitaApiEnums import *
from Api.KitaApi import KitaApi, Symbol
from Api.Position import Position
from Api.CoFu import *
from Api.Constants import *
from BrokerProvider.TradePaper import TradePaper
from BrokerProvider.QuoteCtraderCache import QuoteCtraderCache


class CsvAction:
    def __init__(self):
        self.time: datetime = datetime.min
        self.type: TradeType = TradeType.Buy
        self.symbol_name: str = ""
        self.volume: float = 0.0
        self.price: float = 0.0
        self.is_to_open: bool = True
        self.is_to_close: bool = False
        self.wkn: str = ""
        self.vorgang: str = ""
        self.is_executed: bool = False
        self.id: str = ""


class CsvTrader(KitaApi):
    """
    CsvTrader Bot - Ported from C# CsvTrader.
    Trades based on CSV files listing trades.
    Specifically supports the NewsTrader format (Trade_Zusammenfassung.csv).
    """

    version: str = "CsvTrader V1.2"

    # Parameters
    symbol_name_param: str = "vis"  # "vis" for chart symbol, "all" for all symbols in CSV
    csv_filenames: str = "Trade_Zusammenfassung.csv"
    csv_directory: str = r"C:\Users\HMz\Documents\Source\NewsTrader\Trades"
    
    profit_mode: ProfitMode = ProfitMode.Lots
    value: float = -1.0  # -1 means use volume from CSV
    direction: TradeDirection = TradeDirection.Both

    def __init__(self):
        super().__init__()
        self.csv_actions: List[CsvAction] = []
        # Map symbol name to its actions and current index
        self.symbol_actions: dict[str, List[CsvAction]] = {}
        self.symbol_indices: dict[str, int] = {}
        self.symbol_map: dict[str, Symbol] = {}

    def on_init(self) -> None:
        # Load CSV actions
        self.load_csv_actions()
        
        # Determine the "vis" symbol name if in vis mode
        # In KitaTrader, the 'vis' symbol is the one passed to the bot runner.
        
        quote_provider = QuoteCtraderCache(data_rate=0, parameter="C:/Users/HMz/Documents/cAlgo/Cache")
        trade_provider = TradePaper("")

        # Identify symbols needed from CSV
        distinct_names = set(a.symbol_name for a in self.csv_actions)
        
        # If in 'vis' mode, we'll wait for the runner to trigger on_tick for a specific symbol.
        if self.symbol_name_param.lower() != "all" and self.symbol_name_param.lower() != "vis":
            # Direct symbol name provided
            error, symbol = self.request_symbol(self.symbol_name_param, quote_provider, trade_provider)
            if error == "":
                self.symbol_map[self.symbol_name_param.lower()] = symbol
        elif self.symbol_name_param.lower() == "all":
            for name in distinct_names:
                # We try to request every symbol in the CSV
                error, symbol = self.request_symbol(name, quote_provider, trade_provider)
                if error == "":
                    self.symbol_map[name.lower()] = symbol
        
        # Organize actions per symbol
        for action in self.csv_actions:
            s_name = action.symbol_name.lower()
            if s_name not in self.symbol_actions:
                self.symbol_actions[s_name] = []
                self.symbol_indices[s_name] = 0
            self.symbol_actions[s_name].append(action)
        
        # Sort each list
        for s_name in self.symbol_actions:
            self.symbol_actions[s_name].sort(key=lambda x: x.time)

    def load_csv_actions(self):
        full_path = os.path.join(self.csv_directory, self.csv_filenames)
        if not os.path.exists(full_path):
            print(f"CSV file not found: {full_path}")
            return

        print(f"Parsing CSV: {full_path}")
        with open(full_path, 'r', encoding='utf-8') as f:
            first_line = f.readline()
            f.seek(0)
            
            if "Datum;Uhrzeit;Vorgang" in first_line:
                # NewsTrader format
                reader = csv.DictReader(f, delimiter=';')
                for i, row in enumerate(reader):
                    try:
                        time_str = f"{row['Datum']} {row['Uhrzeit']}"
                        dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                        
                        action = CsvAction()
                        action.time = dt
                        action.vorgang = row['Vorgang'].lower()
                        # Use Name as primary symbol identifier
                        action.symbol_name = row['Name']
                        action.wkn = row['WKN']
                        action.volume = float(row['Stueckzahl'])
                        action.price = float(row['Kurs'])
                        action.id = f"{action.wkn}_{i}"
                        
                        if action.vorgang == "kauf":
                            action.is_to_open = True
                            action.is_to_close = False
                            action.type = TradeType.Buy
                        elif action.vorgang == "verkauf":
                            action.is_to_open = False
                            action.is_to_close = True
                            action.type = TradeType.Sell
                        else:
                            continue
                            
                        self.csv_actions.append(action)
                    except Exception as e:
                        # Skip errors (some might be headers or empty lines)
                        pass
            else:
                # Fallback implementation for original formats if needed...
                # (For now, prioritizing the user's NewsTrader format)
                pass

    def on_tick(self, symbol: Symbol) -> None:
        if symbol.is_warm_up:
            return

        s_name = symbol.name.lower()
        
        # Check if we have actions for this symbol (or similar name)
        # Try exact match first
        actions = self.symbol_actions.get(s_name)
        
        # If no exact match, try broad match
        if actions is None:
            for csv_name in self.symbol_actions:
                if csv_name in s_name or s_name in csv_name:
                    actions = self.symbol_actions[csv_name]
                    s_name = csv_name # Pin it for this symbol
                    break
        
        if actions is None:
            return

        current_time = self.time # Use api.time
        idx = self.symbol_indices.get(s_name, 0)
        
        while idx < len(actions):
            action = actions[idx]
            
            if current_time >= action.time:
                self.execute_action(action, symbol)
                idx += 1
            else:
                break
        
        self.symbol_indices[s_name] = idx

    def execute_action(self, action: CsvAction, symbol: Symbol):
        if action.is_executed:
            return

        # Direction filter
        if action.type == TradeType.Buy and self.direction == TradeDirection.Short:
            return
        if action.type == TradeType.Sell and self.direction == TradeDirection.Long:
            # Note: In a Long strategy, Sell means Close.
            pass

        if action.is_to_open:
            volume = action.volume
            if volume > 0:
                volume = symbol.normalize_volume_in_units(volume)
            
            if self.value != -1:
                # Override volume if parameter is set (Value in lots)
                volume = symbol.normalize_volume_in_units(self.value * symbol.lot_size)
            
            if volume <= 0:
                print(f"[{self.time}] Skipping {action.type} on {symbol.name} due to zero volume.")
                action.is_executed = True
                return

            print(f"[{self.time}] Replaying {action.type} on {symbol.name} (WKN: {action.wkn}) vol={volume}")
            position = symbol.trade_provider.execute_market_order(
                action.type,
                symbol.name,
                volume,
                label=f"{self.version};{action.wkn}"
            )
            if position:
                action.is_executed = True
            else:
                # Failed to open? Might be no liquidity or market closed in backtest.
                pass
        
        elif action.is_to_close:
            # Find a matching position to close
            matching_pos = None
            for pos in self.positions:
                if pos.symbol.name == symbol.name:
                    # Match by WKN in label
                    if action.wkn in pos.label:
                        matching_pos = pos
                        break
            
            if matching_pos:
                print(f"[{self.time}] Replaying Close for {symbol.name} (WKN: {action.wkn})")
                symbol.trade_provider.close_position(matching_pos)
                action.is_executed = True
            else:
                # If no matching position, check if we should open a SHORT if directed
                if self.direction == TradeDirection.Both or self.direction == TradeDirection.Short:
                    volume = symbol.normalize_volume_in_units(action.volume)
                    print(f"[{self.time}] No position to close, opening SHORT on {symbol.name} (WKN: {action.wkn})")
                    symbol.trade_provider.execute_market_order(
                        TradeType.Sell,
                        symbol.name,
                        volume,
                        label=f"{self.version};{action.wkn}"
                    )
                action.is_executed = True

    def on_stop(self) -> None:
        print(f"{self.version} stopped.")

