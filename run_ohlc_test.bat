@echo off
setlocal enabledelayedexpansion

set CTRADER_CLI="C:\Users\HMz\AppData\Local\Spotware\cTrader\abb70432efbee65d18af69e79fe8efe1\ctrader-cli.exe"
set ROBOT_ALGO="C:\Users\HMz\Documents\cAlgo\Sources\Robots\OHLCTestBot.algo"
set PWD_FILE="C:\Users\HMz\Documents\Source\cTraderTools\Apps\PyDownload\password.txt"
set LOG_DIR="C:\Users\HMz\Documents\cAlgo\Logfiles"

REM All output goes to log files, no stdout
(
echo ========================================
echo OHLC Tick Test - C# vs Python Comparison
echo Testing ticks only (2 days: 1/12/2025 to 3/12/2025)
echo ========================================
echo.
echo Step 1: Running C# OHLCTestBot...
echo ----------------------------------------
echo NOTE: C# test uses account 5166098 (traderLogin) with CTID Quantrosoft
echo       Python test uses account folder: demo_19011fd1
echo       Both should use the same Pepperstone account for accurate comparison
echo       Cache location: C:\Users\HMz\AppData\Roaming\Spotware\Cache\pepperstone
echo.
) >> "%LOG_DIR%\test_run.log" 2>&1

%CTRADER_CLI% backtest %ROBOT_ALGO% --start=01/12/2025 --end=03/12/2025 --data-mode=ticks --balance=10000 --commission=0 --spread=0 --ctid=Quantrosoft --pwd-file=%PWD_FILE% --account=5166098 --broker=Pepperstone --symbol=AUDNZD --period=m1 --full-access >> "%LOG_DIR%\csharp_ohlc_test_output.txt" 2>&1

if errorlevel 1 (
    echo ERROR: C# backtest failed! >> "%LOG_DIR%\test_run.log" 2>&1
    exit /b 1
)

(
echo C# Backtest completed.
echo.
echo Step 2: Running Python OHLCTestBot...
echo ----------------------------------------
) >> "%LOG_DIR%\test_run.log" 2>&1

cd /d "%~dp0"
python TestOHLC.py >> "%LOG_DIR%\python_ohlc_test_output.txt" 2>&1

if errorlevel 1 (
    echo ERROR: Python backtest failed! >> "%LOG_DIR%\test_run.log" 2>&1
    exit /b 1
)

(
echo Python Backtest completed.
echo.
echo Step 3: Comparing tick values...
echo ----------------------------------------
echo NOTE: Tick comparison script needs to be created or use compare_logs.py
echo       Log files:
echo       - C#: Check csharp_ohlc_test_output.txt for tick log location
echo       - Python: %LOG_DIR%\OHLC_Test_Python_Ticks.csv
echo.
echo ========================================
echo Tick test complete!
echo ========================================
) >> "%LOG_DIR%\test_run.log" 2>&1

