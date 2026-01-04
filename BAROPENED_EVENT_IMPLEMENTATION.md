# BarOpened Event Implementation - Summary

## Date: 2026-01-03

## Objective
Create a 1:1 lock step port from C# bot to Python bot, implementing BarOpened events similar to cTrader CLI, and ensuring both bots log bars and indicators only on BarOpened events.

## Changes Implemented

### 1. ✅ Created BarOpenedEventArgs Class
**File**: `KitaTrader/Api/BarOpenedEventArgs.py`
- Matches cTrader API: `cAlgo.API.BarOpenedEventArgs`
- Provides `Bars` property to access the Bars object that triggered the event

### 2. ✅ Added BarOpened Event to Bars Class
**File**: `KitaTrader/Api/Bars.py`
- Added `_bar_opened_handlers` list to store event subscribers
- Added `BarOpened` property that supports `+=` and `-=` operators (matching C# syntax)
- Added `_fire_bar_opened_event()` method that fires the event when a new bar is created
- Event is fired in `bars_on_tick()` when `is_new_bar` is True (new bar started)

### 3. ✅ Updated Python OHLCTestBot to Use BarOpened Events
**File**: `KitaTrader/Robots/OHLCTestBot.py`
- Subscribes to BarOpened events for M1, H1, and H4 bars in `on_start()`
- Added event handlers:
  - `Bars_M1_BarOpened()` - Logs M1 bars and indicators
  - `Bars_H1_BarOpened()` - Logs H1 bars and indicators
  - `Bars_H4_BarOpened()` - Logs H4 bars and indicators (including BB)
- Removed bar logging from `on_tick()` - now only logs ticks
- All bar and indicator logging happens only in BarOpened event handlers
- Added helper methods:
  - `_log_bar_with_indicators()` - Logs a bar with SMA values
  - `_create_bb_indicators()` - Creates Bollinger Bands indicators
  - `_log_h4_indicators()` - Logs H4 indicator values (BB and SMA)

### 4. ✅ Updated Date Ranges
**File**: `KitaTrader/OHLCTestConsole.py`
- Updated date range to: from 1.12.25 to 3.12.25 (including)
- `BacktestStart = 01.12.2025`
- `BacktestEnd = 04.12.2025` (end of day 3, exclusive)

## API Usage Example

### Python (Matching C# Syntax)
```python
def on_start(self, symbol: Symbol):
    # Subscribe to BarOpened event
    self.m_bars_m1.BarOpened += self.Bars_M1_BarOpened
    
def Bars_M1_BarOpened(self, args: BarOpenedEventArgs):
    bars = args.Bars
    new_bar = bars.Last(0)  # Current bar
    closed_bar = bars.Last(1)  # Previous closed bar
    # Log bars and indicators here
```

### C# (Reference)
```csharp
protected override void OnStart()
{
    Bars.BarOpened += Bars_BarOpened;
}

private void Bars_BarOpened(BarOpenedEventArgs args)
{
    var newBar = args.Bars.LastBar;  // Or args.Bars.Last(0)
    var closedBar = args.Bars.Last(1);  // Previous closed bar
    // Log bars and indicators here
}
```

## Event Firing Behavior

- Event is fired when a new bar opens (previous bar is now closed)
- Event is NOT fired for the first bar (no previous bar to close)
- Event is fired in `bars_on_tick()` when `is_new_bar` is True
- **CRITICAL**: Event is ONLY fired after `BacktestStartUtc` - NOT during warmup period
- All subscribed handlers are called synchronously
- Errors in handlers are logged but don't stop execution

## Warmup Period vs Backtest Start - Architecture

**IMPORTANT**: The warmup period and backtest start are handled differently:

### Internal Processing (Warmup Period)
- **Starts at**: `WarmupStart` (e.g., 2025-11-24)
- **Purpose**: Internal processing only - building bars, calculating indicators
- **What happens**:
  - Ticks are processed from `WarmupStart` onwards
  - Bars are built incrementally from ticks
  - Indicators are calculated (for warmup)
  - **NO bot event handlers are called** during warmup

### Bot Event Handlers (Backtest Start)
- **Starts at**: `BacktestStart` (e.g., 2025-12-01)
- **Purpose**: Bot logic execution - trading decisions, logging
- **What happens**:
  - `OnTick()` is called only when `symbol.time >= BacktestStartUtc`
  - `OnBar()` is called only when `symbol.time >= BacktestStartUtc`
  - `BarOpened` events fire only when `symbol.time >= BacktestStartUtc`
  - Bot's event handlers receive data only from `BacktestStart` onwards

### Implementation Details

1. **In `KitaApi.do_tick()`**:
   - Checks `symbol.is_warm_up` (set in `symbol_on_tick()` based on `time < BacktestStartUtc`)
   - If `is_warm_up == True`: Skip calling `robot.on_tick()` - only process internally
   - If `is_warm_up == False`: Call `robot.on_tick()` - bot logic executes

2. **In `Bars._fire_bar_opened_event()`**:
   - Checks `symbol.is_warm_up` before firing event
   - Only fires `BarOpened` events when `not symbol.is_warm_up` (i.e., `time >= BacktestStartUtc`)

3. **In `Symbol.symbol_on_tick()`**:
   - Sets `self.is_warm_up = self.time < self.api.robot._BacktestStartUtc`
   - This flag is used throughout to determine if we're in warmup or backtest phase

### Example Timeline

```
WarmupStart: 2025-11-24 00:00:00 UTC
  ↓
  [Internal Processing Only]
  - Ticks processed: ✓
  - Bars built: ✓
  - Indicators calculated: ✓
  - OnTick() called: ✗
  - OnBar() called: ✗
  - BarOpened events: ✗
  ↓
BacktestStart: 2025-12-01 00:00:00 UTC
  ↓
  [Bot Event Handlers Active]
  - Ticks processed: ✓
  - Bars built: ✓
  - Indicators calculated: ✓
  - OnTick() called: ✓
  - OnBar() called: ✓
  - BarOpened events: ✓
  ↓
BacktestEnd: 2025-12-05 00:00:00 UTC (exclusive)
```

## Date Range Filtering - Platform-Controlled

**CRITICAL ARCHITECTURE PRINCIPLE**: Date range filtering (start/end time behavior) is controlled **"under the hood"** by the platform/API layer, **NOT** by the bot code itself.

### Platform Responsibility
- The platform (cTrader CLI/GUI or KitaTrader API) handles all date range filtering based on:
  - CLI parameters: `--start` and `--end` (for cTrader CLI)
  - Python API: `BacktestStart` and `BacktestEnd` properties (for KitaTrader)
- The platform ensures that:
  - Ticks outside the date range are never sent to the bot
  - Bars outside the date range are never created or passed to event handlers
  - Event handlers (`OnTick`, `OnBar`, `BarOpened`) only receive data within the specified range

### Bot Code Responsibility
- **Bot code must NOT contain hardcoded date ranges**
- **Bot code must NOT filter by date/time in event handlers**
- Bot code should assume that any data it receives is already within the valid date range
- Bot code should log/process all bars/ticks that reach it, trusting the platform has already filtered appropriately

### Implementation Details

**Python (KitaTrader)**:
- `KitaApi.do_init()` converts `BacktestStart` and `BacktestEnd` to UTC and stores as `_BacktestStartUtc` and `_BacktestEndUtc`
- `KitaApi.do_tick()` stops processing when `symbol.time > _BacktestEndUtc`
- `Bars._fire_bar_opened_event()` suppresses events when new bar open time (when previous bar closes) is `>= _BacktestEndUtc`
- Bot event handlers (`on_tick`, `on_bar`, `BarOpened`) only receive data within `[BacktestStartUtc, BacktestEndUtc)`

**C# (cTrader)**:
- cTrader CLI/GUI handles date filtering based on `--start` and `--end` parameters
- The cTrader platform ensures `OnTick`, `OnBar`, and `BarOpened` events only fire for data within the specified range
- Bot code should not contain `mStartDate`/`mEndDate` fields or date filtering logic

### Date Range Configuration

Both bots use the same date range (configured at platform level):
- **WarmupStart**: 2025-11-24 00:00:00 UTC (internal processing only)
- **BacktestStart**: 2025-12-01 00:00:00 UTC (bot event handlers start)
- **BacktestEnd**: 2025-12-03 00:00:00 UTC (inclusive - includes all of Dec 3)
  - Internally converted to: 2025-12-04 00:00:00 UTC (exclusive) for platform filtering

## Next Steps for C# Bot

The C# bot needs to be updated to:
1. Subscribe to `Bars.BarOpened` events for M1, H1, and H4 bars
2. Move bar and indicator logging from `OnTick()` to `Bars_BarOpened()` event handlers
3. Update date range to match Python bot (1.12.25 to 3.12.25 including)
4. Ensure logging only happens on BarOpened events

**C# Bot Location**: `C:\Users\HMz\Documents\cAlgo\Sources\Robots\OHLCTestBot\OHLCTestBot\OHLCTestBot.cs`

## Files Modified

1. ✅ `KitaTrader/Api/BarOpenedEventArgs.py` - New file
2. ✅ `KitaTrader/Api/Bars.py` - Added BarOpened event support
3. ✅ `KitaTrader/Robots/OHLCTestBot.py` - Updated to use BarOpened events
4. ✅ `KitaTrader/OHLCTestConsole.py` - Updated date range

## Verification

To verify the implementation:
1. Run Python bot: `python OHLCTestConsole.py`
2. Check that bars and indicators are logged only when BarOpened events fire
3. Verify date range filtering works correctly
4. Compare with C# bot output (after C# bot is updated)
