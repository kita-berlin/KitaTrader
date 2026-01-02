@echo off
set CTRADER_CLI="C:\Users\HMz\AppData\Local\Spotware\cTrader\abb70432efbee65d18af69e79fe8efe1\ctrader-cli.exe"
set ROBOT_ALGO="C:\Users\HMz\Documents\cAlgo\Sources\Robots\Kanga2\Kanga2\bin\Debug\net6.0-windows\Kanga2.algo"
set PWD_FILE="C:\Users\HMz\Documents\Source\cTraderTools\Apps\PyDownload\password.txt"
set CONFIG_FILE="G:\Meine Ablage\ConfigFiles\Kanga2\Kanga2, AUDNZD h1 Long.cbotset"

echo Running C# Kanga2 Backtest...
%CTRADER_CLI% backtest %ROBOT_ALGO% %CONFIG_FILE% --start=01/12/2025 --end=30/12/2025 --data-mode=ticks --balance=10000 --commission=0 --spread=0 --ctid=Quantrosoft --pwd-file=%PWD_FILE% --account=5166098 --symbol=AUDNZD --period=h1 --full-access

echo C# Backtest finished.
