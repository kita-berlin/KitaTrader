from __future__ import annotations
from datetime import datetime
from typing import List, Callable, Optional, Any
import pytz
from Api.TimeSeries import TimeSeries
from Api.DataSeries import DataSeries
from Api.KitaApiEnums import *
from Api.Bar import Bar
from Api.ring_buffer import Ringbuffer
from Api.BarOpenedEventArgs import BarOpenedEventArgs


class Bars:
    # bars are not indexed; only time and data series are indexed
    # Do not use bars.Last().open_time; Use bars.open_times.Last() instead

    # Members
    # region
    open_times: TimeSeries

    open_bids: DataSeries
    high_bids: DataSeries
    low_bids: DataSeries
    close_bids: DataSeries
    volume_bids: DataSeries

    open_asks: DataSeries
    high_asks: DataSeries
    low_asks: DataSeries
    close_asks: DataSeries
    volume_asks: DataSeries

    symbol_name: str  # Gets the symbol name
    timeframe_seconds: int  # Get the timeframe in seconds
    look_back: int  # Gets the look back period.#
    is_new_bar: bool = False  # if true, the current tick is the first tick of a new bar
    read_index: int = 0  # relative index of the current bar to be read
    count: int = 0  # number of bars appended so far; if count == size, the buffer is completely filled
    _symbol: Optional[Any] = None  # Reference to parent Symbol object (for accessing digits, etc.)
    _bar_opened_handlers: List[Callable[[BarOpenedEventArgs], None]] = []  # Event handlers for BarOpened event

    @property
    def size(self) -> int:  # Gets the number of bars.#
        if self.timeframe_seconds == 0:
            # For tick data, use list length (not ringbuffer)
            return len(self.open_times_list) if hasattr(self, 'open_times_list') else 0
        else:
            # For bar data, use ringbuffer size
            return self.open_times._size if self.open_times else 0

    # endregion

    def __init__(self, symbol_name: str, timeframe_seconds: int, look_back: int, symbol: Any = None):
        self.symbol_name = symbol_name
        self.timeframe_seconds = timeframe_seconds
        self._symbol = symbol  # Store reference to Symbol for accessing digits, etc.
        self.read_index = -1  # gets a +1 at symbol_on_tick before accessing the data
        self.count = 0  # Initialize count to 0 - bars will be built incrementally from ticks
        self._bar_opened_handlers = []  # Initialize event handlers list
        self._bar_opened_event = None  # Cached BarOpenedEvent instance
        
        # Calculate maximum period requirement for ring buffer size
        # Start with look_back (if provided), will be updated when indicators are attached
        # New Architecture: Ring buffer size = max(period) + 1 bar
        self._max_period_requirement = max(look_back, 0)
        self.look_back = self._max_period_requirement + 1
        
        if timeframe_seconds > 0:
            # size = max(period) + 1 bar
            size = self.look_back
            # If look_back is still 0 (only happens if requested in on_init before indicators),
            # we will resize later or start with a default if needed. 
            # But usually indicators are created in on_init/on_start.
            if size == 0:
                size = 1000 # Default fallback if nothing specified yet
            self._bar_buffer: Ringbuffer[Bar] = Ringbuffer[Bar](size)
        else:
            # For tick data, look_back doesn't apply, no storage needed
            # Tick data is not stored - ticks are processed one at a time from stream
            # TICKS NEVER GO INTO RINGBUFFERS - only bars and indicators use ringbuffers
            # For temporary day objects (from get_day_at_utc), use regular Python lists, NOT ringbuffers
            self.look_back = 0
            self._bar_buffer = None  # No bar buffer for tick data

        # Create DataSeries views for API compatibility (indicators expect DataSeries)
        # For bar data: extract values from Ringbuffer[Bar] - uses ringbuffers
        # For tick data: use regular Python lists (NOT ringbuffers) for temporary day-by-day loading
        # Note: The main rate_data Bars object (used during backtest) does not store ticks,
        # but temporary day objects (from get_day_at_utc) need to store ticks temporarily in lists
        if timeframe_seconds > 0:
            # Bar data: full OHLCV DataSeries (uses ringbuffers)
            self.open_times = TimeSeries(self, size)
            self.open_bids = DataSeries(self, size)
            self.open_asks = DataSeries(self, size)
            self.volume_bids = DataSeries(self, size)
            self.volume_asks = DataSeries(self, size)
            self.high_bids = DataSeries(self, size)
            self.low_bids = DataSeries(self, size)
            self.close_bids = DataSeries(self, size)
            self.high_asks = DataSeries(self, size)
            self.low_asks = DataSeries(self, size)
            self.close_asks = DataSeries(self, size)
        else:
            # Tick data: use regular Python lists (NOT ringbuffers) for temporary storage
            # High/low/close don't exist for tick data
            # TICKS NEVER GO INTO RINGBUFFERS - use simple lists for temporary day loading
            from typing import List
            self.open_times_list: List[datetime] = []  # Regular list, not ringbuffer
            self.open_bids_list: List[float] = []  # Regular list, not ringbuffer (float prices)
            self.open_asks_list: List[float] = []  # Regular list, not ringbuffer (float prices)
            self.volume_bids_list: List[float] = []  # Regular list, not ringbuffer
            self.volume_asks_list: List[float] = []  # Regular list, not ringbuffer
            # Create dummy DataSeries/TimeSeries for API compatibility (but they won't be used)
            # These are only for type compatibility, actual data is in lists above
            self.open_times = TimeSeries(self, 0)  # Dummy, not used
            self.open_bids = DataSeries(self, 0)  # Dummy, not used
            self.open_asks = DataSeries(self, 0)  # Dummy, not used
            self.volume_bids = DataSeries(self, 0)  # Dummy, not used
            self.volume_asks = DataSeries(self, 0)  # Dummy, not used
            # High/low/close not used for tick data
            self.high_bids = None  # type: ignore
            self.low_bids = None  # type: ignore
            self.close_bids = None  # type: ignore
            self.high_asks = None  # type: ignore
            self.low_asks = None  # type: ignore
            self.close_asks = None  # type: ignore
    
    def update_max_period_requirement(self, period: int) -> None:
        """
        Update the maximum period requirement and recalculate look_back and ring buffer size.
        New Architecture: Ring buffer size = max(period) + 1 bar.
        Resizes the buffers if they are already initialized.
        """
        if period > self._max_period_requirement:
            self._max_period_requirement = period
            new_look_back = self._max_period_requirement + 1
            
            if self.timeframe_seconds > 0 and new_look_back > self.look_back:
                old_look_back = self.look_back
                self.look_back = new_look_back
                
                # Resize existing buffer if it exists
                if hasattr(self, '_bar_buffer') and self._bar_buffer:
                    old_buffer = self._bar_buffer
                    self._bar_buffer = Ringbuffer[Bar](self.look_back)
                    # Copy data from old buffer (from oldest to newest)
                    for i in range(old_buffer._count - 1, -1, -1):
                        self._bar_buffer.add(old_buffer[i])
                    
                    # Resize all DataSeries/TimeSeries (references are preserved!)
                    self.open_times.resize(self.look_back)
                    self.open_bids.resize(self.look_back)
                    self.open_asks.resize(self.look_back)
                    self.volume_bids.resize(self.look_back)
                    self.volume_asks.resize(self.look_back)
                    self.high_bids.resize(self.look_back)
                    self.low_bids.resize(self.look_back)
                    self.close_bids.resize(self.look_back)
                    self.high_asks.resize(self.look_back)
                    self.low_asks.resize(self.look_back)
                    self.close_asks.resize(self.look_back)
                    
                    self.count = self._bar_buffer._count
    def append(
        self,
        time: datetime,
        open_bid: float,
        high_bid: float,
        low_bid: float,
        close_bid: float,
        volume_bid: float,
        open_ask: float,
        high_ask: float,
        low_ask: float,
        close_ask: float,
        volume_ask: float,
    ) -> None:
        # Create a complete Bar object (OHLCV as one element)
        import math
        # Handle NaN values in volume
        vol = volume_bid if not math.isnan(volume_bid) else 0.0
        bar = Bar(
            open_time=time,
            open=open_bid,  # Use bid for main values
            high=high_bid,
            low=low_bid,
            close=close_bid,
            tick_volume=int(vol)
        )
        
        # Tick data (timeframe_seconds == 0): Only store temporarily for day-by-day loading
        # TICKS NEVER GO INTO RINGBUFFERS - use regular Python lists
        # The main rate_data Bars object (used during backtest) does not store ticks
        # But temporary day objects (from quote providers) need to store ticks for reading
        if self.timeframe_seconds == 0:
            # Store ticks temporarily in regular lists (NOT ringbuffers)
            # This is different from rate_data which doesn't call append() for tick data
            self.open_times_list.append(time)
            self.open_bids_list.append(open_bid)
            self.open_asks_list.append(open_ask)
            self.volume_bids_list.append(volume_bid)
            self.volume_asks_list.append(volume_ask)
            self.count = len(self.open_times_list)
            return
        
        # Bar data: use Ringbuffer[Bar] - each bar (OHLCV) is one element
        self._bar_buffer.add(bar)  # Ringbuffer.add() - overwrites oldest when full
        self.count = self._bar_buffer._count
        
        # Calculate write position for DataSeries (where the newest bar is stored)
        size = self.size
        if self.count < size:
            # Buffer not full yet - newest bar is at count - 1
            write_pos = self.count - 1
        else:
            # Buffer full - calculate write position from Ringbuffer
            # Ringbuffer._position points to the NEXT write position
            # So the newest bar is at (_position - 1) % size
            write_pos = (self._bar_buffer._position - 1) % size
        
        # read_index must match write_pos so that last() can correctly access the newest bar
        self.read_index = write_pos if self.count > 0 else -1
        
        # Also update DataSeries views for API compatibility
        # Extract values from the Ringbuffer[Bar] and update DataSeries
        if self.count > 0:
            self.open_times.append_ring(time, write_pos)
            self.open_bids.append_ring(open_bid, write_pos)
            self.open_asks.append_ring(open_ask, write_pos)
            self.volume_bids.append_ring(volume_bid, write_pos)
            self.volume_asks.append_ring(volume_ask, write_pos)
            self.high_bids.append_ring(high_bid, write_pos)
            self.low_bids.append_ring(low_bid, write_pos)
            self.close_bids.append_ring(close_bid, write_pos)
            self.high_asks.append_ring(high_ask, write_pos)
            self.low_asks.append_ring(low_ask, write_pos)
            self.close_asks.append_ring(close_ask, write_pos)

    def add(
        self,
        time: datetime,
        open_bid: float,
        high_bid: float,
        low_bid: float,
        close_bid: float,
        volume_bid: float,
        open_ask: float,
        high_ask: float,
        low_ask: float,
        close_ask: float,
        volume_ask: float,
    ) -> None:

        # xxxxx todo

        self.read_index = (self.read_index + 1) % self.open_times._size  # type: ignore
        if self.count < self.open_times._size:  # type: ignore
            self.count += 1

    def bars_on_tick(self, time: datetime, bid: float = None, ask: float = None, tick_volume: int = 1) -> None:
        """
        Build bars incrementally from ticks.
        Workflow: Internal Tick -> call bars_on_tick to evolve bars -> indicators -> user's OnTick
        
        This builds bars from ticks - indicator calculation happens separately in symbol_on_tick().
        Bars are NEVER preloaded - they are always built incrementally from ticks.
        """
        self.is_new_bar = False

        # Bars should ALWAYS be built incrementally from ticks (never preloaded)
        if bid is None or ask is None:
            # If bid/ask not provided, cannot build bars - skip
            return
        
        if self.timeframe_seconds == 0:
            # Tick data - no bar building needed
            return
        
        # Calculate bar start time for this timeframe
        from datetime import timedelta
        import pytz
        
        # Calculate bar start time (aligned to timeframe)
        bar_start_time = self._calculate_bar_start_time(time, self.timeframe_seconds)
        
        # Check if we need to start a new bar
        if self.count == 0:
            # First bar - start new bar
            self._start_new_bar(bar_start_time, bid, ask, tick_volume)
            self.is_new_bar = True
            self.read_index = self.count - 1  # Point to the new bar
            # Note: Don't fire BarOpened event for the first bar (no previous bar to close)
        else:
            # Check if current bar is still active
            # Get the current bar's start time from DataSeries
            if self.count > 0:
                # Use DataSeries to get current bar time (read_index points to current bar)
                current_bar_time = self.open_times.last(0) if self.read_index >= 0 else None
            else:
                current_bar_time = None
            
            if current_bar_time is None or bar_start_time > current_bar_time:
                # CRITICAL: Check if this new bar would be at or after BacktestEndUtc BEFORE starting it
                # This matches C# behavior - stop before creating a bar that is >= BacktestEndUtc
                if self._symbol and hasattr(self._symbol, 'api') and hasattr(self._symbol.api, 'robot'):
                    if hasattr(self._symbol.api.robot, '_BacktestEndUtc'):
                        backtest_end_utc = self._symbol.api.robot._BacktestEndUtc
                        # Ensure both are timezone-aware for proper comparison
                        if backtest_end_utc.tzinfo is None:
                            backtest_end_utc = backtest_end_utc.replace(tzinfo=pytz.UTC)
                        if bar_start_time.tzinfo is None:
                            bar_start_time = bar_start_time.replace(tzinfo=pytz.UTC)
                        # If bar_start_time >= BacktestEndUtc, don't start this bar
                        if bar_start_time >= backtest_end_utc:
                            # Set flag to signal stop and return early
                            self._symbol._should_stop_processing = True
                            return  # Don't start this bar
                
                # New bar started - the previous bar is now closed
                # Start new bar (read_index will be updated to point to the new bar)
                self._start_new_bar(bar_start_time, bid, ask, tick_volume)
                self.is_new_bar = True
                # read_index is updated in _start_new_bar via append()
                # For bar data, read_index points to newest bar (Ringbuffer[0] = newest)
                # This is set in append() for bar data
                
                # Fire BarOpened event (matching cTrader API behavior)
                # Event is fired when a new bar opens (previous bar is now closed)
                # BUT only after BacktestStartUtc - warmup period is for internal processing only
                # OnTick, OnBar, and BarOpened events should only fire after BacktestStart
                # Also check if the new bar's open time (when previous bar closes) is < BacktestEndUtc
                # This prevents logging bars that close at or after the backtest end time
                should_fire = False
                if self._symbol and hasattr(self._symbol, 'is_warm_up'):
                    # Use is_warm_up flag (set in symbol_on_tick based on time < BacktestStartUtc)
                    should_fire = not self._symbol.is_warm_up
                elif self._symbol and hasattr(self._symbol, 'api') and hasattr(self._symbol.api, 'robot'):
                    # Fallback: check time directly against BacktestStartUtc
                    if hasattr(self._symbol.api.robot, '_BacktestStartUtc'):
                        should_fire = time >= self._symbol.api.robot._BacktestStartUtc
                
                # Additional check: don't fire if the new bar's open time (when previous bar closes) is >= BacktestEndUtc
                # This ensures bars that close at or after the backtest end time are not logged
                if should_fire and self._symbol and hasattr(self._symbol, 'api') and hasattr(self._symbol.api, 'robot'):
                    if hasattr(self._symbol.api.robot, '_BacktestEndUtc'):
                        # bar_start_time is when the new bar opens, which is when the previous bar closes
                        # If bar_start_time >= BacktestEndUtc, the previous bar closed at or after the end time
                        if bar_start_time >= self._symbol.api.robot._BacktestEndUtc:
                            should_fire = False
                
                if should_fire:
                    self._fire_bar_opened_event()
            else:
                # Update current bar (evolve it) - read_index points to the current forming bar
                self._update_current_bar(bid, ask, tick_volume)
        
        return
    
    def _calculate_bar_start_time(self, time: datetime, timeframe_seconds: int) -> datetime:
        """Calculate the bar start time for a given tick time and timeframe"""
        from datetime import timedelta
        import pytz
        
        # For H4 (14400 seconds), align to NY 17:00 ET (21:00 UTC during EDT, 22:00 UTC during EST)
        # For H1 (3600 seconds), align to hour boundaries
        # For M1 (60 seconds), align to minute boundaries
        
        if timeframe_seconds >= 86400:  # Daily or larger
            # Align to day start (00:00:00 UTC)
            return time.replace(hour=0, minute=0, second=0, microsecond=0)
        elif timeframe_seconds >= 3600:  # Hourly or larger
            hours = timeframe_seconds // 3600
            if hours == 4:
                # H4: align to NY 17:00 ET (21:00 UTC during EDT, 22:00 UTC during EST)
                # Use the same logic as _resample() in Symbol.py
                ny_tz = pytz.timezone('America/New_York')
                ny_dt = time.astimezone(ny_tz)
                # Anchor to 17:00 NY of the same day
                anchor_ny = ny_dt.replace(hour=17, minute=0, second=0, microsecond=0)
                # Convert back to UTC
                anchor_utc = anchor_ny.astimezone(pytz.UTC)
                
                # Calculate hours since anchor
                hours_since_anchor = (time - anchor_utc).total_seconds() / 3600.0
                if hours_since_anchor < 0:
                    # Before anchor today, use previous day's anchor
                    anchor_utc = anchor_utc - timedelta(days=1)
                    hours_since_anchor = (time - anchor_utc).total_seconds() / 3600.0
                
                # Round down to nearest 4-hour boundary
                bar_number = int(hours_since_anchor // 4)
                bar_start_utc = anchor_utc + timedelta(hours=bar_number * 4)
                return bar_start_utc.replace(second=0, microsecond=0)
            else:
                # Other hourly timeframes: align to hour
                return time.replace(minute=0, second=0, microsecond=0)
        else:
            # Minute timeframes: align to minute boundaries
            minutes = timeframe_seconds // 60
            minute = (time.minute // minutes) * minutes
            return time.replace(minute=minute, second=0, microsecond=0)
    
    def _start_new_bar(self, bar_start_time: datetime, bid: float, ask: float, tick_volume: int = 1) -> None:
        """Start a new bar with the given time and prices"""
        # append() will update read_index automatically
        self.append(
            bar_start_time,
            bid,  # open_bid
            bid,  # high_bid (initial)
            bid,  # low_bid (initial)
            bid,  # close_bid (initial)
            float(tick_volume),  # volume_bid (initial)
            ask,  # open_ask
            ask,  # high_ask (initial)
            ask,  # low_ask (initial)
            ask,  # close_ask (initial)
            float(tick_volume),  # volume_ask (initial)
        )
    
    def _update_current_bar(self, bid: float, ask: float, tick_volume: int = 1) -> None:
        """Update the current bar with new tick prices"""
        # Only works for bar data (timeframe_seconds > 0)
        # Tick data is not stored, so this is never called for tick data
        if self.read_index < 0 or self.read_index >= self.count:
            return
        
        if self._bar_buffer is None:
            return  # No bar buffer (tick data or not initialized)
        
        # Update the current bar in Ringbuffer[Bar]
        if self.count > 0:
            current_bar = self._bar_buffer.last()  # Get newest bar (Ringbuffer[0])
            if current_bar:
                # Update bar values in Ringbuffer
                if bid > current_bar.High:
                    current_bar.High = bid
                if bid < current_bar.Low:
                    current_bar.Low = bid
                current_bar.Close = bid
                current_bar.TickVolume += tick_volume
                
                # Update DataSeries for bar data
                # Ringbuffer uses relative indexing: 0 = newest (current) bar
                if bid > self.high_bids.data[0]:
                    self.high_bids.data[0] = bid
                if ask > self.high_asks.data[0]:
                    self.high_asks.data[0] = ask
                if bid < self.low_bids.data[0]:
                    self.low_bids.data[0] = bid
                if ask < self.low_asks.data[0]:
                    self.low_asks.data[0] = ask
                self.close_bids.data[0] = bid
                self.close_asks.data[0] = ask
                self.volume_bids.data[0] += 1.0
                self.volume_asks.data[0] += 1.0
    
    def high_changed(self, current_price: float) -> bool:
        """Check if current price creates a new high (higher than bar's current high)"""
        if self.read_index < 0 or self.read_index >= self.count:
            return False
        # Tick data doesn't have high/low - only bar data does
        if self.timeframe_seconds == 0 or not hasattr(self, 'high_bids'):
            return False
        current_high = self.high_bids.data[self.read_index]
        # If current price is higher than the bar's high, we found a new high
        return current_price > current_high
    
    def low_changed(self, current_price: float) -> bool:
        """Check if current price creates a new low (lower than bar's current low)"""
        if self.read_index < 0 or self.read_index >= self.count:
            return False
        # Tick data doesn't have high/low - only bar data does
        if self.timeframe_seconds == 0 or not hasattr(self, 'low_bids'):
            return False
        current_low = self.low_bids.data[self.read_index]
        # If current price is lower than the bar's low, we found a new low
        return current_price < current_low
    
    
    # region
    
    @property
    def OpenPrices(self) -> DataSeries:
        """Gets the Open price bars data (cTrader API: Bars.OpenPrices)"""
        return self.open_bids
    
    @property
    def HighPrices(self) -> DataSeries:
        """Gets the High price bars data (cTrader API: Bars.HighPrices)"""
        return self.high_bids
    
    @property
    def LowPrices(self) -> DataSeries:
        """Gets the Low price bars data (cTrader API: Bars.LowPrices)"""
        return self.low_bids
    
    @property
    def ClosePrices(self) -> DataSeries:
        """Gets the Close price bars data (cTrader API: Bars.ClosePrices)"""
        return self.close_bids
    
    @property
    def OpenTimes(self) -> TimeSeries:
        """Gets the open bar time data (cTrader API: Bars.OpenTimes)"""
        return self.open_times
    
    @property
    def TickVolumes(self) -> DataSeries:
        """Gets the Tick volumes data (cTrader API: Bars.TickVolumes)"""
        return self.volume_bids
    
    def _fire_bar_opened_event(self):
        """Fire BarOpened event to all subscribed handlers"""
        if self._bar_opened_handlers and len(self._bar_opened_handlers) > 0:
            args = BarOpenedEventArgs(self)
            for handler in self._bar_opened_handlers:
                try:
                    handler(args)
                except Exception as e:
                    # Log error but don't stop execution
                    import sys
                    if hasattr(sys, '_getframe'):
                        caller = sys._getframe(2)
                        if caller and hasattr(caller, 'f_locals') and 'self' in caller.f_locals:
                            pass
    
    class BarOpenedEvent:
        """Event object that supports += and -= operators"""
        def __init__(self, bars: Bars):
            self._bars = bars
        
        def __iadd__(self, handler: Callable[[BarOpenedEventArgs], None]):
            """Subscribe to the event: Bars.BarOpened += handler"""
            if handler not in self._bars._bar_opened_handlers:
                self._bars._bar_opened_handlers.append(handler)
            return self
        
        def __isub__(self, handler: Callable[[BarOpenedEventArgs], None]):
            """Unsubscribe from the event: Bars.BarOpened -= handler"""
            if handler in self._bars._bar_opened_handlers:
                self._bars._bar_opened_handlers.remove(handler)
            return self
    
    class BarOpenedDescriptor:
        """Descriptor that handles += and -= operations for BarOpened event"""
        def __get__(self, obj, objtype=None):
            if obj is None:
                return self
            if obj._bar_opened_event is None:
                obj._bar_opened_event = Bars.BarOpenedEvent(obj)
            return obj._bar_opened_event
        
        def __set__(self, obj, value):
            # Allow setting to support += operator
            # The __iadd__ returns self, so we just ignore the set
            pass
    
    BarOpened = BarOpenedDescriptor()
    
    def Last(self, index: int) -> Bar:
        """
        Gets the bar from the end of the collection (cTrader API: Bars.Last(int index)).
        
        Args:
            index: Number of bars ago (0 = current bar, 1 = previous closed bar, etc.)
        
        Returns:
            Bar object with OpenTime, Open, High, Low, Close, TickVolume properties
        
        Example:
            prevBar = bars.Last(1)  # Previous closed bar
            barTime = prevBar.OpenTime
            barOpen = prevBar.Open
        """
        if index < 0 or index >= self.count:
            # Return empty bar if index is out of range
            return Bar()
        
        # For bar data, try to read from Ringbuffer[Bar] if available
        if self._bar_buffer is not None and self.count > 0:
            # Ringbuffer[0] = newest bar, Ringbuffer[1] = second newest, etc.
            bar = self._bar_buffer[index] if index < self.count else None
            if bar:
                return Bar(
                    open_time=bar.OpenTime,
                    open=bar.Open,
                    high=bar.High,
                    low=bar.Low,
                    close=bar.Close,
                    tick_volume=bar.TickVolume
                )
        
        # For tick data, use lists (NOT ringbuffers)
        if self.timeframe_seconds == 0:
            # Tick data stored in lists
            if hasattr(self, 'open_times_list') and len(self.open_times_list) > index:
                list_idx = len(self.open_times_list) - 1 - index  # Convert to list index (0 = oldest)
                if list_idx >= 0 and list_idx < len(self.open_times_list):
                    open_time = self.open_times_list[list_idx]
                    open_price = self.open_bids_list[list_idx]
                    tick_volume = int(self.volume_bids_list[list_idx] + self.volume_asks_list[list_idx])
                    # For ticks, open = high = low = close (single price point)
                    return Bar(
                        open_time=open_time,
                        open=open_price,
                        high=open_price,
                        low=open_price,
                        close=open_price,
                        tick_volume=tick_volume
                    )
            return Bar()  # No tick data available
        
        # For bar data, use DataSeries/TimeSeries last() methods (ringbuffers)
        # last(0) = current bar, last(1) = previous bar, etc.
        if self.open_times is None:
            return Bar()  # No data
        
        open_time = self.open_times.last(index) if index < self.count else datetime.min
        open_price = self.open_bids.last(index) if index < self.count else 0.0
        high_price = self.high_bids.last(index) if index < self.count else 0.0
        low_price = self.low_bids.last(index) if index < self.count else 0.0
        close_price = self.close_bids.last(index) if index < self.count else 0.0
        tick_volume = int(self.volume_bids.last(index) + self.volume_asks.last(index)) if index < self.count else 0
        
        return Bar(
            open_time=open_time,
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            tick_volume=tick_volume
        )
    
    # endregion


# end of file
