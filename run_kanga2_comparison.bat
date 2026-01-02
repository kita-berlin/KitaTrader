@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Kanga2 C# vs Python Comparison Test
echo ========================================
echo.

set CTRADER_CLI="C:\Users\HMz\AppData\Local\Spotware\cTrader\abb70432efbee65d18af69e79fe8efe1\ctrader-cli.exe"
set ROBOT_ALGO="C:\Users\HMz\Documents\cAlgo\Sources\Robots\Kanga2\Kanga2\bin\Debug\net6.0-windows\Kanga2.algo"
set PWD_FILE="C:\Users\HMz\Documents\Source\cTraderTools\Apps\PyDownload\password.txt"
set CONFIG_FILE="G:\Meine Ablage\ConfigFiles\Kanga2\Kanga2, AUDNZD h1 Long.cbotset"
set LOG_DIR="C:\Users\HMz\Documents\cAlgo\Logfiles"

echo Step 1: Running C# Kanga2 Backtest...
echo ----------------------------------------
%CTRADER_CLI% backtest %ROBOT_ALGO% %CONFIG_FILE% --start=01/12/2025 --end=30/12/2025 --data-mode=ticks --balance=10000 --commission=0 --spread=0 --ctid=Quantrosoft --pwd-file=%PWD_FILE% --account=5166098 --symbol=AUDNZD --period=h1 --full-access

if errorlevel 1 (
    echo ERROR: C# backtest failed!
    exit /b 1
)

echo.
echo C# Backtest completed.
echo.

echo Step 2: Running Python Kanga2 Backtest...
echo ----------------------------------------
cd /d "%~dp0"
python MainConsole.py

if errorlevel 1 (
    echo ERROR: Python backtest failed!
    exit /b 1
)

echo.
echo Python Backtest completed.
echo.

echo Step 3: Comparing log files...
echo ----------------------------------------
python compare_kanga2_detailed.py

echo.
echo ========================================
echo Comparison complete!
echo ========================================

