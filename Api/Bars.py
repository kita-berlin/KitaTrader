from __future__ import annotations
from datetime import datetime
from Api.TimeSeries import TimeSeries
from Api.DataSeries import DataSeries
from Api.KitaApiEnums import *
from Api.Bar import Bar
from Api.ring_buffer import Ringbuffer


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
    data_mode: DataMode
    _symbol: 'Symbol' = None  # Reference to parent Symbol object (for accessing digits, etc.)

    @property
    def size(self) -> int:  # Gets the number of bars.#
        return len(self.open_times.data)  # type: ignore

    # endregion

    def __init__(self, symbol_name: str, timeframe_seconds: int, look_back: int, data_mode: DataMode, symbol: 'Symbol' = None):
        self.symbol_name = symbol_name
        self.timeframe_seconds = timeframe_seconds
        self.data_mode = data_mode
        self._symbol = symbol  # Store reference to Symbol for accessing digits, etc.
        self.read_index = -1  # gets a +1 at symbol_on_tick before accessing the data
        self.count = 0  # Initialize count to 0 - bars will be built incrementally from ticks
        
        # Calculate maximum period requirement for ring buffer size
        # Start with look_back (if provided), will be updated when indicators are attached
        # Ring buffer size = max(period) + 2 days buffer (same as warmup period calculation)
        self._max_period_requirement = max(look_back, 0)  # Start with provided look_back or 0
        
        # Calculate look_back and ring buffer size: max(period) + 2 days buffer (in bars)
        if timeframe_seconds > 0:
            from Api.Constants import Constants
            # 2 days buffer in bars = (2 * SEC_PER_DAY) / timeframe_seconds
            two_days_bars = int((2 * Constants.SEC_PER_DAY) / timeframe_seconds)
            # look_back = max(period) + 2 days buffer
            self.look_back = max(self._max_period_requirement, two_days_bars)
            # Ring buffer size = max(period) + 2 days buffer (same as look_back)
            size = self.look_back
        else:
            # For tick data, look_back doesn't apply, no ring buffer needed
            self.look_back = 0
            size = 1000  # Not used for tick data

        # Use Ringbuffer[Bar] to store complete bars (each bar with OHLCV is one element)
        # For tick data (timeframe_seconds=0), don't use ring buffer (grows as needed)
        if timeframe_seconds == 0:
            # Tick data: use sequential storage (no ring buffer)
            self._bar_buffer: list[Bar] = []  # Sequential list for ticks
            self._use_ring_buffer = False
        else:
            # Bar data: use Ringbuffer[Bar] - each bar (OHLCV) is one element
            self._bar_buffer: Ringbuffer[Bar] = Ringbuffer[Bar](size)
            self._use_ring_buffer = True

        # Create DataSeries views for API compatibility (indicators expect DataSeries)
        # These will extract values from the Ringbuffer[Bar]
        self.open_times = TimeSeries(self, size)
        self.open_bids = DataSeries(self, size)
        self.open_asks = DataSeries(self, size)
        self.volume_bids = DataSeries(self, size)
        self.volume_asks = DataSeries(self, size)
        if 0 != timeframe_seconds:
            self.high_bids = DataSeries(self, size)
            self.low_bids = DataSeries(self, size)
            self.close_bids = DataSeries(self, size)

            self.high_asks = DataSeries(self, size)
            self.low_asks = DataSeries(self, size)
            self.close_asks = DataSeries(self, size)
    
    def update_max_period_requirement(self, period: int) -> None:
        """
        Update the maximum period requirement and recalculate look_back and ring buffer size.
        Ring buffer size = max(period) + 2 days buffer (same as warmup period calculation).
        """
        if period > self._max_period_requirement:
            self._max_period_requirement = period
            # Recalculate look_back and ring buffer size: max(period) + 2 days buffer
            if self.timeframe_seconds > 0:
                from Api.Constants import Constants
                # 2 days buffer in bars = (2 * SEC_PER_DAY) / timeframe_seconds
                two_days_bars = int((2 * Constants.SEC_PER_DAY) / self.timeframe_seconds)
                # look_back = max(period) + 2 days buffer
                self.look_back = max(self._max_period_requirement, two_days_bars)
                # Ring buffer size should also be updated, but resizing is complex
                # For now, we'll just update the requirement - resizing would require:
                # 1. Creating new Ringbuffer with new size
                # 2. Copying existing data
                # 3. Updating all DataSeries/TimeSeries sizes
                # TODO: Implement buffer resizing if needed (complex due to ring buffer)
                # Note: In practice, this should be called during initialization before bars are built

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
        
        if self.timeframe_seconds == 0:
            # Tick data: sequential append (grows as needed, no ring buffer)
            self._bar_buffer.append(bar)  # type: ignore - list.append for ticks
            self.count = len(self._bar_buffer)  # Sync count with list length
            # DO NOT set read_index here - it should remain at -1 until symbol_on_tick() starts reading
            # read_index will be incremented in symbol_on_tick() from -1 to 0, 1, 2, ... up to count-1
            
            # Also update DataSeries for API compatibility
            self.open_times.append(time)
            self.open_bids.append(open_bid)
            self.open_asks.append(open_ask)
            self.volume_bids.append(volume_bid)
            self.volume_asks.append(volume_ask)
        else:
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
        if 0 != self.timeframe_seconds:
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

    def bars_on_tick(self, time: datetime, bid: float = None, ask: float = None) -> None:
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
            self._start_new_bar(bar_start_time, bid, ask)
            self.is_new_bar = True
            self.read_index = self.count - 1  # Point to the new bar
        else:
            # Check if current bar is still active
            # For ring buffer, read_index points to the current (forming) bar
            # Get the current bar's start time from the ring buffer
            if self._use_ring_buffer:
                # Ring buffer mode: get current bar from Ringbuffer[Bar]
                if self.count > 0:
                    current_bar = self._bar_buffer.last()  # Get newest bar (Ringbuffer[0])
                    current_bar_time = current_bar.OpenTime if current_bar else None
                else:
                    current_bar_time = None
            else:
                # Sequential mode: use DataSeries
                current_bar_time = self.open_times.data[self.read_index] if self.read_index >= 0 and self.read_index < self.count else None
            
            if current_bar_time is None or bar_start_time > current_bar_time:
                # New bar started - the previous bar is now closed
                # Start new bar (read_index will be updated to point to the new bar)
                # Debug logging for H4 bars
                if self.timeframe_seconds == 14400:
                    import sys
                    if hasattr(sys, '_getframe'):
                        caller = sys._getframe(1)
                        if caller and hasattr(caller, 'f_locals') and 'self' in caller.f_locals:
                            symbol = caller.f_locals.get('self')
                            if symbol and hasattr(symbol, 'api') and hasattr(symbol.api, '_debug_log'):
                                symbol.api._debug_log(f"[bars_on_tick] H4 new bar: time={time}, bar_start_time={bar_start_time}, current_bar_time={current_bar_time}, count={self.count}")
                self._start_new_bar(bar_start_time, bid, ask)
                self.is_new_bar = True
                # read_index is updated in _start_new_bar via append()
                if self._use_ring_buffer:
                    self.read_index = 0  # Ringbuffer[0] is newest
                else:
                    self.read_index = self.count - 1  # Point to the new forming bar
            else:
                # Update current bar (evolve it) - read_index points to the current forming bar
                self._update_current_bar(bid, ask)
        
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
    
    def _start_new_bar(self, bar_start_time: datetime, bid: float, ask: float) -> None:
        """Start a new bar with the given time and prices"""
        # append() will update read_index automatically
        self.append(
            bar_start_time,
            bid,  # open_bid
            bid,  # high_bid (initial)
            bid,  # low_bid (initial)
            bid,  # close_bid (initial)
            1.0,  # volume_bid (initial)
            ask,  # open_ask
            ask,  # high_ask (initial)
            ask,  # low_ask (initial)
            ask,  # close_ask (initial)
            1.0,  # volume_ask (initial)
        )
    
    def _update_current_bar(self, bid: float, ask: float) -> None:
        """Update the current bar with new tick prices"""
        # For ring buffer, update the current bar in Ringbuffer[Bar] and DataSeries
        if self._use_ring_buffer:
            # Ring buffer mode: update the current bar (Ringbuffer[0])
            if self.count > 0:
                current_bar = self._bar_buffer.last()  # Get newest bar (Ringbuffer[0])
                if current_bar:
                    # Update bar values
                    if bid > current_bar.High:
                        current_bar.High = bid
                    if bid < current_bar.Low:
                        current_bar.Low = bid
                    current_bar.Close = bid
                    current_bar.TickVolume += 1
                    
                    # Also update DataSeries for API compatibility
                    # For ring buffer, read_index=0 points to newest bar
                    # Calculate write position: newest bar is at (position - 1) % size when full, or count-1 when not full
                    if self.count < self.size:
                        write_pos = self.count - 1
                    else:
                        write_pos = (self._bar_buffer._position - 1) % self.size
                    
                    if bid > self.high_bids.data[write_pos]:
                        self.high_bids.data[write_pos] = bid
                    if ask > self.high_asks.data[write_pos]:
                        self.high_asks.data[write_pos] = ask
                    if bid < self.low_bids.data[write_pos]:
                        self.low_bids.data[write_pos] = bid
                    if ask < self.low_asks.data[write_pos]:
                        self.low_asks.data[write_pos] = ask
                    self.close_bids.data[write_pos] = bid
                    self.close_asks.data[write_pos] = ask
                    self.volume_bids.data[write_pos] += 1.0
                    self.volume_asks.data[write_pos] += 1.0
        else:
            # Sequential mode: update using read_index
            if self.read_index < 0 or self.read_index >= self.count:
                return
            
            # Update high
            if bid > self.high_bids.data[self.read_index]:
                self.high_bids.data[self.read_index] = bid
            if ask > self.high_asks.data[self.read_index]:
                self.high_asks.data[self.read_index] = ask
            
            # Update low
            if bid < self.low_bids.data[self.read_index]:
                self.low_bids.data[self.read_index] = bid
            if ask < self.low_asks.data[self.read_index]:
                self.low_asks.data[self.read_index] = ask
            
            # Update close (always)
            self.close_bids.data[self.read_index] = bid
            self.close_asks.data[self.read_index] = ask
            
            # Update volume
            self.volume_bids.data[self.read_index] += 1.0
            self.volume_asks.data[self.read_index] += 1.0
    
    def high_changed(self, current_price: float) -> bool:
        """Check if current price creates a new high (higher than bar's current high)"""
        if self.read_index < 0 or self.read_index >= self.count:
            return False
        current_high = self.high_bids.data[self.read_index]
        # If current price is higher than the bar's high, we found a new high
        return current_price > current_high
    
    def low_changed(self, current_price: float) -> bool:
        """Check if current price creates a new low (lower than bar's current low)"""
        if self.read_index < 0 or self.read_index >= self.count:
            return False
        current_low = self.low_bids.data[self.read_index]
        # If current price is lower than the bar's low, we found a new low
        return current_price < current_low
    
    # cTrader API compatibility properties and methods
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
        
        # For ring buffer mode, read directly from Ringbuffer[Bar] for accuracy
        if self._use_ring_buffer and self.count > 0:
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
        
        # Fallback: Use DataSeries/TimeSeries last() methods
        # last(0) = current bar, last(1) = previous bar, etc.
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
