# KitaTrader OHLCV Verification Results

## Summary
This document tracks the verification status of OHLCV bar generation between KitaTrader (Python) and cTrader (C#).

## Verification Status

### ✅ **Completed Verifications**

| Timeframe | Summer (July 2025) | Winter (Dec/Jan 2025) | Notes |
|-----------|-------------------|----------------------|-------|
| **M1** | ✅ VERIFIED | ⏳ Pending | Perfect match (1-day test) |
| **H1** | ✅ VERIFIED | ⏳ Pending | Perfect match (10-day test) |
| **H3** | ✅ VERIFIED | ✅ VERIFIED | Perfect OHLC match, alignment confirmed |
| **H4** | ✅ VERIFIED | ✅ VERIFIED | Perfect OHLC match, alignment confirmed |
| **Ticks** | ⏳ Pending | ⏳ Pending | - |
| **Daily** | ⏳ Pending | ⏳ Pending | - |

### Key Findings

#### 1. **17:00 NY Time Anchor** ✅
- **Confirmed**: cTrader aligns H3, H4, and Daily bars to 17:00 New York Time
- **Implementation**: Dynamic origin calculation in `Symbol.py` `_resample()` method
- **Coverage**: Applied to all timeframes ≥ 1 hour (3600 seconds)

#### 2. **Seasonal Offset Handling** ✅
- **Summer (EDT, UTC-4)**: 17:00 NY = 21:00 UTC
  - H4 Grid: 21:00, 01:00, 05:00, 09:00, 13:00, 17:00
  - H3 Grid: 00:00, 03:00, 06:00, 09:00, 12:00, 15:00, 18:00, 21:00
  
- **Winter (EST, UTC-5)**: 17:00 NY = 22:00 UTC
  - H4 Grid: 22:00, 02:00, 06:00, 10:00, 14:00, 18:00
  - H3 Grid: 22:00, 01:00, 04:00, 07:00, 10:00, 13:00, 16:00, 19:00

#### 3. **Volume Calculation** ✅
- **Formula**: `volume = volume_bids + volume_asks`
- **Matches**: cTrader's `TickVolume` (sum of bid and ask tick counts)

#### 4. **Critical Bug Fixes**

##### A. Stale Cache File Handling ✅
- **Problem**: H1/H3 bar files from previous date ranges prevented fallback to tick resampling
- **Solution**: Check if bars were actually loaded for requested period, raise FileNotFoundError if count unchanged
- **Location**: `Symbol.py` `_load_bars()` method

##### B. Timezone Awareness ✅
- **Problem**: Comparison errors between offset-naive and offset-aware datetimes
- **Solution**: Ensure all datetime objects are UTC-aware before comparison
- **Location**: `Symbol.py` `load_datarate_and_bars()` and `KitaApi.py` `do_stop()`

##### C. Division by Zero ✅
- **Problem**: `max_equity` division when no ticks processed
- **Solution**: Check for datetime.min and None before calculations
- **Location**: `KitaApi.py` `do_stop()`

### Test Data Locations

#### Summer Tests (July 2025)
- **Date Range**: July 4-24, 2025 (various subsets)
- **Cache**: `C:\Users\HMz\AppData\Roaming\Spotware\Cache\pepperstone\BacktestingCache\V1\demo_19011fd1\AUDNZD\t1\202507*.zticks`

#### Winter Tests (December 2025 / January 2025)
- **Date Range**: December 29-30, 2025 / January 14-18, 2025
- **Cache**: `C:\Users\HMz\AppData\Roaming\Spotware\Cache\pepperstone\BacktestingCache\V1\demo_19011fd1\AUDNZD\t1\202512*.zticks` and `202501*.zticks`

### Code Changes

#### Modified Files
1. **`Api/Symbol.py`**
   - Added dynamic origin calculation for H1+ timeframes based on 17:00 NY Time
   - Added fallback check for stale cache files
   - Added timezone awareness handling

2. **`Api/KitaApi.py`**
   - Added safety checks for datetime operations in `do_stop()`

3. **`Robots/PriceVerifyBot.py`**
   - Updated volume calculation: `volume_bids + volume_asks`
   - Configurable for different timeframes

4. **`compare_logs.py`**
   - Added regex to handle comma decimal separators from C# logs

### Usage

#### Running Manual Tests
```bash
# 1. Configure dates in MainConsole.py
# 2. Configure timeframe in PriceVerifyBot.py
# 3. Configure C# test in run_cli_verification.bat
# 4. Run tests
.\run_cli_verification.bat
python MainConsole.py

# 5. Compare results
python compare_logs.py
```

#### Running Comprehensive Suite
```bash
python comprehensive_verification.py
```

### References
- cTrader Cache Structure: `{DataPath}\{symbol}\t1\{YYYYMMDD}.zticks`
- Python Bar Cache: `{DataPath}\{symbol}\{timeframe}\{YYYYMMDD}_quote.zip`
- Log Output: `C:\Users\HMz\Documents\cAlgo\Logfiles\`

---
**Last Updated**: 2026-01-01  
**Status**: Indicator verification complete.

## Indicator Verification (H1 AUDNZD July 2025)

| Indicator | Status | Convergence | Notes |
| :--- | :--- | :--- | :--- |
| **EMA(14)** | ✅ VERIFIED | Bar 30 | Matches cTrader exactly after convergence. |
| **SMA(20)** | ✅ VERIFIED | Bar 1 | Perfect match. |
| **Bollinger Bands** | ✅ VERIFIED | Bar 20 | Perfect match. |
| **Vidya(14, 0.65)** | ✅ VERIFIED | Bar 30 | Perfect match. |
| **MACD(26, 12)** | ✅ VERIFIED | Bar 40 | Perfect match. |
| **MACD Signal(9)** | ✅ VERIFIED | Bar 50 | Perfect match. |
| **MACD Histogram** | ✅ VERIFIED | Bar 50 | Matches (difference calculation MACD - Signal). |
| **RSI(14)** | ✅ VERIFIED | Bar 50 | Wilder's smoothing implementation matches (diff < 0.0001). |

### Convergence and History ✅
The discrepancies observed earlier were primarily due to insufficient historical data for indicator warm-up. By modifying `Symbol.py` to load ticks starting from `AllDataStartUtc` (Jan 1, 2025), even for a July 10, 2025 backtest, the indicators are fully converged at the start of the verification period.

### Key Implementation Notes
- **RSI**: Uses Wilder's smoothing with SMA initialization for the first `periods` bars.
- **MACD Histogram**: cTrader's `MACDHistogram` indicator properties: `Histogram` is the MACD line, the visual bars are `Histogram - Signal`. Python implementation now aligns with this.
- **Precision**: 5 decimal places matching for all indicators (standard cTrader display precision).

### Open Issues
- None. Core indicators are now verified and identical to cTrader.
