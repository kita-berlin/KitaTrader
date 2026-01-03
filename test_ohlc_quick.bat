@echo off
REM Quick test - Run C# bot and save output
REM IMPORTANT: C# bot MUST run FIRST to download data to Spotware cache
REM            Python bot then uses the SAME Spotware cache folder
echo ========================================
echo OHLC TestBot - C# vs Python Comparison
echo ========================================
echo.
echo Step 1: Running C# bot (downloads data)...

set CTRADER_CLI="C:\Users\HMz\AppData\Local\Spotware\cTrader\abb70432efbee65d18af69e79fe8efe1\ctrader-cli.exe"
set ROBOT_ALGO="C:\Users\HMz\Documents\cAlgo\Sources\Robots\OHLCTestBot.algo"
set PWD_FILE="C:\Users\HMz\Documents\Source\cTraderTools\Apps\PyDownload\password.txt"
set LOG_DIR=C:\Users\HMz\Documents\cAlgo\Logfiles

REM Build C# bot to ensure latest code (No Filtering) is used
echo Building OHLCTestBot (dotnet)...
dotnet build "C:\Users\HMz\Documents\cAlgo\Sources\Robots\OHLCTestBot\OHLCTestBot\OHLCTestBot.csproj" -c Release > %LOG_DIR%\dotnet_build.log 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Build failed! Check dotnet_build.log
    exit /b 1
)

REM Dotnet build automatically updates the .algo file in the Sources/Robots folder

REM Run C# bot (1 day for quick test)
%CTRADER_CLI% backtest %ROBOT_ALGO% --start=01/12/2025 --end=04/12/2025 --data-mode=ticks --balance=10000 --commission=0 --spread=0 --ctid=Quantrosoft --pwd-file=%PWD_FILE% --account=5166098 --broker=Pepperstone --symbol=AUDNZD --period=m1 --full-access > %LOG_DIR%\csharp_ohlc_output.txt 2>&1

echo C# bot completed. Output saved to: %LOG_DIR%\csharp_ohlc_output.txt
echo.
echo Step 2: Extracting C# ticks from console output...
cd /d "%~dp0"
python extract_csharp_ticks.py

echo.
echo Step 3: Running Python bot (uses same Spotware cache)...
python TestOHLC.py

echo.
echo Step 4: Comparing outputs...
python compare_ohlc_ticks.py

echo.
echo ========================================
echo Test Complete!
echo ========================================
REM pause
