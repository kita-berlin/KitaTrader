@echo off
setlocal enabledelayedexpansion

echo ========================================
echo OHLC Bars Test - C# vs Python Comparison
echo ========================================
echo.

set CTRADER_CLI="C:\Users\HMz\AppData\Local\Spotware\cTrader\abb70432efbee65d18af69e79fe8efe1\ctrader-cli.exe"
set ROBOT_ALGO="C:\Users\HMz\Documents\cAlgo\Sources\Robots\OHLCTestBot.algo"
set PWD_FILE="C:\Users\HMz\Documents\Source\cTraderTools\Apps\PyDownload\password.txt"
set LOG_DIR="C:\Users\HMz\Documents\cAlgo\Logfiles"

echo Step 1: Running C# OHLCTestBot...
echo ----------------------------------------
echo NOTE: C# test uses account 5166098 (traderLogin) with CTID Quantrosoft
echo       Python test uses account folder: demo_19011fd1
echo       Both should use the same Pepperstone account for accurate comparison
echo       Cache location: C:\Users\HMz\AppData\Roaming\Spotware\Cache\pepperstone
echo.
%CTRADER_CLI% backtest %ROBOT_ALGO% --start=01/12/2025 --end=06/12/2025 --data-mode=ticks --balance=10000 --commission=0 --spread=0 --ctid=Quantrosoft --pwd-file=%PWD_FILE% --account=5166098 --symbol=AUDNZD --period=h4 --full-access > "%LOG_DIR%\csharp_ohlc_test_output.txt" 2>&1

if errorlevel 1 (
    echo ERROR: C# backtest failed!
    exit /b 1
)

echo.
echo C# Backtest completed.
echo.

echo Step 2: Running Python OHLCTestBot...
echo ----------------------------------------
cd /d "%~dp0"
python TestOHLC.py > "%LOG_DIR%\python_ohlc_test_output.txt" 2>&1

if errorlevel 1 (
    echo ERROR: Python backtest failed!
    exit /b 1
)

echo.
echo Python Backtest completed.
echo.

echo Step 3: Comparing OHLC bar values for all timeframes (M1, H1, H4)...
echo ----------------------------------------
python "%LOG_DIR%\compare_all_timeframes.py"

echo.
echo Step 4: Comparing SMA values (H4 only)...
echo ----------------------------------------
python "%LOG_DIR%\compare_sma_values.py"

echo.
echo Step 5: Comparing BB values (H4 only)...
echo ----------------------------------------
python "%LOG_DIR%\compare_bb_values.py"

echo.
echo ========================================
echo Comparison complete!
echo ========================================

