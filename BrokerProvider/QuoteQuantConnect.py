"""
QuoteQuantConnect - Data provider for QuantConnect format
Handles second-based OHLCV data with bid/ask from zipped daily files
"""

import os
import zipfile
import csv
from datetime import datetime, timedelta
from Api.KitaApi import KitaApi, Symbol
from Api.Bars import Bars
from Api.QuoteProvider import QuoteProvider


class QuoteQuantConnect(QuoteProvider):
    """
    Quote provider for QuantConnect format data
    
    Expected format:
    - One zip file per day
    - Inside: CSV with second-based OHLCV data
    - Timestamp: Milliseconds since midnight
    - Separate bid/ask data or combined
    
    Data path structure:
    {DataPath}/EURUSD/20250101_quotes.zip
    """
    
    provider_name = "QuoteQuantConnect"
    _assets_file_name: str = "Assets_QuantConnect.csv"

    def __init__(self, data_rate: int, parameter: str = ""):
        """
        Initialize QuantConnect provider
        
        Args:
            data_rate: Data rate in seconds (0=ticks, 1=1sec, 60=1min, etc.)
            parameter: Optional parameter string
        """
        assets_path = os.path.join("Files", self._assets_file_name)
        # Force data_rate to 60 (1 minute) for QuantConnect since we aggregate from seconds
        QuoteProvider.__init__(self, parameter, assets_path, 60)  # Always use 1-minute as base
        self._requested_data_rate = data_rate  # Store original request

    def init_symbol(self, api: KitaApi, symbol: Symbol):
        """Initialize symbol-specific settings"""
        self.api = api
        self.symbol = symbol
        self.data_path = api.DataPath
        
        # For QuantConnect: all symbols in same directory (no subdirectories)
        self.symbol_path = self.data_path
        
        # Check if path exists
        if not os.path.exists(self.symbol_path):
            if hasattr(self, 'api') and self.api:
                self.api._debug_log(f"WARNING: Data path does not exist: {self.symbol_path}")
                self.api._debug_log(f"Expected path: {self.symbol_path}")

    def get_day_at_utc(self, utc: datetime) -> tuple[str, datetime, Bars]:
        """
        Load one day of data (aggregated to minute bars)
        
        Args:
            utc: The date to load
            
        Returns:
            tuple of (error_message, last_datetime, bars_data)
        """
        from Api.KitaApiEnums import Constants
        # Create minute-level bars (60 seconds) instead of tick data
        day_data: Bars = Bars(self.symbol.name, 60, 0)
        self.last_utc = utc.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # WEEKEND HANDLING: Check if this is a weekend day (Saturday=5, Sunday=6)
        weekday = utc.weekday()
        if weekday >= 5:  # Saturday or Sunday
            # Return empty data for weekends (no error - forex markets are closed)
            if hasattr(self, 'api') and self.api:
                self.api._debug_log(f"[INFO] Skipping weekend: {utc.strftime('%Y-%m-%d %A')}")
            return "", self.last_utc, day_data
        
        # Filename format: YYYYMMDD_quote.zip
        possible_filenames = [
            f"{utc.year:04}{utc.month:02d}{utc.day:02d}_quote.zip",
        ]
        
        zip_path = None
        for filename in possible_filenames:
            test_path = os.path.join(self.symbol_path, filename)
            if os.path.exists(test_path):
                zip_path = test_path
                break
        
        if zip_path is None:
            # Check if it might be a holiday or missing data
            error_msg = f"No data file found for {utc.strftime('%Y-%m-%d %A')} in {self.symbol_path}"
            if hasattr(self, 'api') and self.api:
                self.api._debug_log(f"[WARN] {error_msg}")
            # Return empty data instead of error to allow continuation
            return "", self.last_utc, day_data
        
        try:
            # Read zip file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Get first CSV file in zip
                csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
                if not csv_files:
                    return f"No CSV file found in {zip_path}", self.last_utc, None  # type: ignore
                
                # Read CSV data
                with zip_ref.open(csv_files[0]) as csv_file:
                    # Decode bytes to string
                    text_data = csv_file.read().decode('utf-8')
                    lines = text_data.strip().split('\n')
                    reader = csv.reader(lines)
                    
                    # Parse CSV (NO HEADER - starts directly with data)
                    # Format: Time(ms), BidO, BidH, BidL, BidC, AskO, AskH, AskL, AskC
                    # 9 columns total: [0]=timestamp, [1-4]=bid OHLC, [5-8]=ask OHLC
                    # Aggregate second data into 1-minute bars
                    
                    current_minute_data = None
                    current_minute = None
                    
                    for row in reader:
                        if not row or len(row) < 9:
                            continue
                        
                        try:
                            # Column 0: Milliseconds since midnight
                            timestamp_ms = int(row[0])
                            
                            # Convert milliseconds since midnight to datetime
                            timestamp = self.last_utc + timedelta(milliseconds=timestamp_ms)
                            minute_timestamp = timestamp.replace(second=0, microsecond=0)
                            
                            # Columns 1-4: Bid OHLC
                            bid_open = float(row[1])
                            bid_high = float(row[2])
                            bid_low = float(row[3])
                            bid_close = float(row[4])
                            
                            # Columns 5-8: Ask OHLC
                            ask_open = float(row[5])
                            ask_high = float(row[6])
                            ask_low = float(row[7])
                            ask_close = float(row[8])
                            
                            # Aggregate into minute bars
                            if current_minute is None or minute_timestamp != current_minute:
                                # New minute - save previous minute bar
                                if current_minute_data is not None:
                                    day_data.append(
                                        current_minute,
                                        current_minute_data['bid_open'],
                                        current_minute_data['bid_high'],
                                        current_minute_data['bid_low'],
                                        current_minute_data['bid_close'],
                                        0.0,  # volume_bid
                                        current_minute_data['ask_open'],
                                        current_minute_data['ask_high'],
                                        current_minute_data['ask_low'],
                                        current_minute_data['ask_close'],
                                        0.0   # volume_ask
                                    )
                                
                                # Start new minute
                                current_minute = minute_timestamp
                                current_minute_data = {
                                    'bid_open': bid_open,
                                    'bid_high': bid_high,
                                    'bid_low': bid_low,
                                    'bid_close': bid_close,
                                    'ask_open': ask_open,
                                    'ask_high': ask_high,
                                    'ask_low': ask_low,
                                    'ask_close': ask_close
                                }
                            else:
                                # Same minute - update OHLC
                                current_minute_data['bid_high'] = max(current_minute_data['bid_high'], bid_high)
                                current_minute_data['bid_low'] = min(current_minute_data['bid_low'], bid_low)
                                current_minute_data['bid_close'] = bid_close
                                current_minute_data['ask_high'] = max(current_minute_data['ask_high'], ask_high)
                                current_minute_data['ask_low'] = min(current_minute_data['ask_low'], ask_low)
                                current_minute_data['ask_close'] = ask_close
                            
                        except (ValueError, IndexError) as e:
                            # Skip malformed rows
                            if hasattr(self, 'api') and self.api:
                                self.api._debug_log(f"Warning: Skipping malformed row: {row[:3]}... Error: {e}")
                            continue
                    
                    # Don't forget the last minute
                    if current_minute_data is not None:
                        day_data.append(
                            current_minute,
                            current_minute_data['bid_open'],
                            current_minute_data['bid_high'],
                            current_minute_data['bid_low'],
                            current_minute_data['bid_close'],
                            0.0,  # volume_bid
                            current_minute_data['ask_open'],
                            current_minute_data['ask_high'],
                            current_minute_data['ask_low'],
                            current_minute_data['ask_close'],
                            0.0   # volume_ask
                        )
            
            if day_data.count == 0:
                if hasattr(self, 'api') and self.api:
                    self.api._debug_log(f"[WARN] No valid data parsed from {zip_path}")
                # Return empty data instead of error
                return "", self.last_utc, day_data
            
            if hasattr(self, 'api') and self.api:
                self.api._debug_log(f"[OK] Loaded {day_data.count:,} minute bars from {utc.strftime('%Y-%m-%d %A')}")
            return "", self.last_utc, day_data
            
        except Exception as e:
            error_msg = f"Error reading {zip_path}: {str(e)}"
            if hasattr(self, 'api') and self.api:
                self.api._debug_log(f"[ERROR] {error_msg}")
            # Return empty data with error message
            return error_msg, self.last_utc, day_data

    def get_first_datetime(self) -> tuple[str, datetime]:
        """
        Find the first available date in the data
        
        Returns:
            tuple of (error_message, first_datetime)
        """
        try:
            # List all files in symbol directory
            if not os.path.exists(self.symbol_path):
                return f"Symbol path not found: {self.symbol_path}", datetime(2000, 1, 1)
            
            files = os.listdir(self.symbol_path)
            zip_files = sorted([f for f in files if f.endswith('.zip')])
            
            if not zip_files:
                return f"No zip files found in {self.symbol_path}", datetime(2000, 1, 1)
            
            # Parse first filename to get date
            first_file = zip_files[0]
            
            # Try to extract date from filename (e.g., 20250101_quote.zip)
            date_str = first_file[:8]  # First 8 characters: YYYYMMDD
            first_date = datetime.strptime(date_str, "%Y%m%d")
            
            return "", first_date
            
        except Exception as e:
            return f"Error finding first date: {str(e)}", datetime(2000, 1, 1)

    def get_highest_data_rate(self) -> int:
        """Return highest available data rate"""
        return 1  # 1 second is our highest resolution (aggregated to minute bars)


# end of file

