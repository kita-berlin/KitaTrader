@echo off
REM Manual Verification Test Runner
REM Tests will be run one at a time with visible progress

echo ================================================================================
echo MANUAL VERIFICATION TEST SUITE
echo ================================================================================
echo.
echo This script will run verification tests one at a time.
echo Press Ctrl+C at any time to stop.
echo.
pause

REM Test 1: Summer M1
echo.
echo ================================================================================
echo TEST 1/10: Summer M1 Bars
echo ================================================================================
echo Configuring for Summer M1 (22-25 July 2025)...
call :configure_test "22.07.2025" "25.07.2025" "22/07/2025" "25/07/2025" "m1" 60 "Summer_M1"
if errorlevel 1 goto :error
echo.
pause

REM Test 2: Summer H1
echo.
echo ================================================================================
echo TEST 2/10: Summer H1 Bars
echo ================================================================================
echo Configuring for Summer H1 (22-25 July 2025)...
call :configure_test "22.07.2025" "25.07.2025" "22/07/2025" "25/07/2025" "h1" 3600 "Summer_H1"
if errorlevel 1 goto :error
echo.
pause

REM Test 3: Summer H3
echo.
echo ================================================================================
echo TEST 3/10: Summer H3 Bars
echo ================================================================================
echo Configuring for Summer H3 (22-25 July 2025)...
call :configure_test "22.07.2025" "25.07.2025" "22/07/2025" "25/07/2025" "h3" 10800 "Summer_H3"
if errorlevel 1 goto :error
echo.
pause

REM Test 4: Summer Daily
echo.
echo ================================================================================
echo TEST 4/10: Summer Daily Bars
echo ================================================================================
echo Configuring for Summer Daily (22-25 July 2025)...
call :configure_test "22.07.2025" "25.07.2025" "22/07/2025" "25/07/2025" "d1" 86400 "Summer_D1"
if errorlevel 1 goto :error
echo.
pause

REM Test 5: Winter M1
echo.
echo ================================================================================
echo TEST 5/10: Winter M1 Bars
echo ================================================================================
echo Configuring for Winter M1 (15-18 January 2025)...
call :configure_test "15.01.2025" "18.01.2025" "15/01/2025" "18/01/2025" "m1" 60 "Winter_M1"
if errorlevel 1 goto :error
echo.
pause

REM Test 6: Winter H1
echo.
echo ================================================================================
echo TEST 6/10: Winter H1 Bars
echo ================================================================================
echo Configuring for Winter H1 (15-18 January 2025)...
call :configure_test "15.01.2025" "18.01.2025" "15/01/2025" "18/01/2025" "h1" 3600 "Winter_H1"
if errorlevel 1 goto :error
echo.
pause

REM Test 7: Winter H3
echo.
echo ================================================================================
echo TEST 7/10: Winter H3 Bars
echo ================================================================================
echo Configuring for Winter H3 (15-18 January 2025)...
call :configure_test "15.01.2025" "18.01.2025" "15/01/2025" "18/01/2025" "h3" 10800 "Winter_H3"
if errorlevel 1 goto :error
echo.
pause

REM Test 8: Winter Daily
echo.
echo ================================================================================
echo TEST 8/10: Winter Daily Bars
echo ================================================================================
echo Configuring for Winter Daily (15-18 January 2025)...
call :configure_test "15.01.2025" "18.01.2025" "15/01/2025" "18/01/2025" "d1" 86400 "Winter_D1"
if errorlevel 1 goto :error
echo.

echo.
echo ================================================================================
echo ALL TESTS COMPLETED!
echo ================================================================================
echo Check VERIFICATION_RESULTS.md for summary
pause
goto :eof

:configure_test
REM Parameters: %1=py_start %2=py_end %3=cs_start %4=cs_end %5=period %6=timeframe %7=name
echo   Updating PriceVerifyBot.py...
python -c "import re; f=open('Robots/PriceVerifyBot.py','r',encoding='utf-8'); c=f.read(); f.close(); c=re.sub(r'log_path = os\.path\.join\(log_dir, \".*?\"\)', 'log_path = os.path.join(log_dir, \"PriceVerify_Python_%~7.csv\")', c); c=re.sub(r'request_bars\(\d+\)', 'request_bars(%~6)', c); c=re.sub(r'get_bars\(\d+\)', 'get_bars(%~6)', c); f=open('Robots/PriceVerifyBot.py','w',encoding='utf-8'); f.write(c); f.close()"

echo   Updating MainConsole.py...
python -c "import re; f=open('MainConsole.py','r',encoding='utf-8'); c=f.read(); f.close(); c=re.sub(r'AllDataStartUtc = datetime\.strptime\(\".*?\", \"%%d\.%%m\.%%Y\"\)', 'AllDataStartUtc = datetime.strptime(\"%~1\", \"%%d.%%m.%%Y\")', c); c=re.sub(r'AllDataEndUtc = datetime\.strptime\(\".*?\", \"%%d\.%%m\.%%Y\"\)', 'AllDataEndUtc = datetime.strptime(\"%~2\", \"%%d.%%m.%%Y\")', c); c=re.sub(r'BacktestStartUtc = datetime\.strptime\(\".*?\", \"%%d\.%%m\.%%Y\"\)', 'BacktestStartUtc = datetime.strptime(\"%~1\", \"%%d.%%m.%%Y\")', c); c=re.sub(r'BacktestEndUtc = datetime\.strptime\(\".*?\", \"%%d\.%%m\.%%Y\"\)', 'BacktestEndUtc = datetime.strptime(\"%~2\", \"%%d.%%m.%%Y\")', c); f=open('MainConsole.py','w',encoding='utf-8'); f.write(c); f.close()"

echo   Running C# backtest...
"C:\Users\HMz\AppData\Local\Spotware\cTrader\abb70432efbee65d18af69e79fe8efe1\ctrader-cli.exe" backtest "C:\Users\HMz\Documents\cAlgo\Sources\Robots\PriceVerifyBot\bin\Release\net6.0\Robots.algo" --start=%~3 --end=%~4 --data-mode=ticks --balance=10000 --commission=0 --spread=0 --ctid=Quantrosoft --pwd-file="C:\Users\HMz\Documents\Source\cTraderTools\Apps\PyDownload\password.txt" --account=5166098 --symbol=AUDNZD --period=%~5 > "C:\Users\HMz\Documents\cAlgo\Logfiles\PriceVerify_CSharp_%~7.txt" 2>&1
if errorlevel 1 (
    echo   ERROR: C# backtest failed!
    exit /b 1
)
echo   C# backtest completed.

echo   Running Python backtest...
python MainConsole.py
if errorlevel 1 (
    echo   ERROR: Python backtest failed!
    exit /b 1
)
echo   Python backtest completed.

echo   Comparing results...
python -c "import re; f=open('compare_logs.py','r',encoding='utf-8'); c=f.read(); f.close(); c=re.sub(r'parse_csharp_log\(r\".*?\"\)', 'parse_csharp_log(r\"C:\\Users\\HMz\\Documents\\cAlgo\\Logfiles\\PriceVerify_CSharp_%~7.txt\")', c); c=re.sub(r'parse_python_log\(r\".*?\"\)', 'parse_python_log(r\"C:\\Users\\HMz\\Documents\\cAlgo\\Logfiles\\PriceVerify_Python_%~7.csv\")', c); f=open('compare_logs.py','w',encoding='utf-8'); f.write(c); f.close()"
python compare_logs.py
echo.
exit /b 0

:error
echo.
echo ================================================================================
echo ERROR: Test failed!
echo ================================================================================
pause
exit /b 1
