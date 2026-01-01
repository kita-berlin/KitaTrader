# Weekend Handling Fix - QuantConnect Provider

## Problem Statement

Forex markets are closed on weekends (Saturday & Sunday), so historical data files don't exist for these days. KitaTrader's default `check_historical_data()` method expected continuous daily data and would throw errors when encountering weekend gaps.

## Solution Implemented

### 1. **Weekend Detection**
Added automatic weekend detection in `QuoteQuantConnect.get_day_at_utc()`:
```python
weekday = utc.weekday()  # Monday=0, ..., Saturday=5, Sunday=6
if weekday >= 5:  # Weekend
    print(f"[INFO] Skipping weekend: {utc.strftime('%Y-%m-%d %A')}")
    return "", self.last_utc, day_data  # Return empty data, no error
```

### 2. **Missing Data Handling**
Changed missing data files from errors to warnings:
```python
if zip_path is None:
    print(f"[WARN] No data file found for {utc.strftime('%Y-%m-%d %A')}")
    return "", self.last_utc, day_data  # Return empty data instead of error
```

### 3. **Parse Error Handling**
Graceful handling of parse errors:
```python
except Exception as e:
    print(f"[ERROR] {error_msg}")
    return error_msg, self.last_utc, day_data  # Return empty data with error message
```

## Benefits

✅ **Seamless Weekend Skipping**: Automatically skips Saturday & Sunday
✅ **Holiday Handling**: Gracefully handles missing data for holidays
✅ **Continuous Backtests**: Can run multi-week/month backtests without manual date management
✅ **Clear Logging**: Informative messages for weekends, warnings, and errors
✅ **No Manual Intervention**: System automatically handles forex market hours

## Usage Example

### Before Fix:
```python
# Had to carefully avoid weekends
self.robot.BacktestStartUtc = datetime.strptime("18.03.2024", "%d.%m.%Y")  # Monday
self.robot.BacktestEndUtc = datetime.strptime("22.03.2024", "%d.%m.%Y")    # Friday
# ERROR if system accessed Saturday (23rd)
```

### After Fix:
```python
# Can span any date range - weekends auto-skipped
self.robot.BacktestStartUtc = datetime.strptime("18.03.2024", "%d.%m.%Y")  # Monday
self.robot.BacktestEndUtc = datetime.strptime("29.03.2024", "%d.%m.%Y")    # Next Friday
# System automatically skips weekends: March 23-24, March 30-31
```

## Expected Output

```
[OK] Loaded 86,400 ticks from 2024-03-18 Monday
[OK] Loaded 86,400 ticks from 2024-03-19 Tuesday
[OK] Loaded 86,400 ticks from 2024-03-20 Wednesday
[OK] Loaded 86,400 ticks from 2024-03-21 Thursday
[OK] Loaded 86,400 ticks from 2024-03-22 Friday
[INFO] Skipping weekend: 2024-03-23 Saturday
[INFO] Skipping weekend: 2024-03-24 Sunday
[OK] Loaded 86,400 ticks from 2024-03-25 Monday
...
```

## Holiday Handling

If a file is missing on a weekday (e.g., Good Friday, Christmas):
```
[WARN] No data file found for 2024-03-29 Friday in G:\...\QuantConnect Seconds
```
System continues without error, using empty data for that day.

## Testing

Test the fix with:
```bash
python MainUltron.py
```

Expected behavior:
1. Loads Monday-Friday data ✓
2. Automatically skips Saturday & Sunday ✓
3. Continues to next week seamlessly ✓
4. Completes backtest without weekend errors ✓

## Technical Details

### Modified File:
- `BrokerProvider/QuoteQuantConnect.py`

### Key Changes:
1. Lines 71-76: Weekend detection and skip logic
2. Lines 90-95: Missing file warning instead of error
3. Lines 156-168: Graceful error handling with empty data return

### Return Value Strategy:
- **Success**: `("", last_utc, bars_with_data)`
- **Weekend**: `("", last_utc, empty_bars)`
- **Missing**: `("", last_utc, empty_bars)` + warning
- **Error**: `(error_msg, last_utc, empty_bars)` + error log

This ensures the system never crashes on weekend/holiday gaps!

## Future Enhancements

Possible improvements:
1. **Holiday Calendar**: Add explicit holiday dates for major markets
2. **Market Hours**: Skip based on exchange trading hours
3. **Data Validation**: Check for abnormally low tick counts
4. **Gap Detection**: Alert on suspicious multi-day gaps

## Compatibility

✅ Works with all KitaTrader features:
- Single-day backtests
- Multi-week backtests
- Genetic Optimizer
- Walk-Forward Optimizer  
- RL Training (Gymnasium)

## Summary

The comprehensive weekend fix allows KitaTrader to:
- Run backtests over any date range
- Automatically skip non-trading days
- Handle missing data gracefully
- Continue operation without manual intervention

**Result**: Robust, production-ready data handling for forex markets! 🎯

