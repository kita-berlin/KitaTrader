@echo off
set CTRADER_CLI="C:\Users\HMz\AppData\Local\Spotware\cTrader\abb70432efbee65d18af69e79fe8efe1\ctrader-cli.exe"
set ROBOT_ALGO="C:\Users\HMz\Documents\cAlgo\Sources\Robots\Robots.algo"
set PWD_FILE="C:\Users\HMz\Documents\Source\cTraderTools\Apps\PyDownload\password.txt"
set LOG_FILE="C:\Users\HMz\Documents\cAlgo\Logfiles\MultiIndicator_Test_CSharp.txt"

%CTRADER_CLI% backtest %ROBOT_ALGO% --start=10/07/2025 --end=20/07/2025 --data-mode=ticks --balance=10000 --commission=0 --spread=0 --ctid=Quantrosoft --pwd-file=%PWD_FILE% --account=5166098 --symbol=AUDNZD --period=h1 > %LOG_FILE% 2>&1
