"""
Compare Kanga2 log files from cTrader CLI and Python version for December 2025
"""
import os
import csv
from pathlib import Path

log_dir = r"C:\Users\HMz\Documents\cAlgo\Logfiles"

# Find latest cTrader CSV log
ctrader_files = sorted(Path(log_dir).glob("Kanga2 *.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
ctrader_csv = ctrader_files[0] if ctrader_files else None

# Find latest Python CSV log (should be similar name)
python_csv = None
if ctrader_csv:
    # Python should create a similar file
    python_csv = ctrader_csv  # They should write to the same file, but let's check

print(f"Comparing log files:")
print(f"  cTrader: {ctrader_csv}")
print(f"  Python:  {python_csv}")
print()

if not ctrader_csv or not os.path.exists(ctrader_csv):
    print("ERROR: cTrader log file not found!")
    exit(1)

# Read cTrader log
ctrader_trades = []
with open(ctrader_csv, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get('Number'):  # Skip empty rows
            ctrader_trades.append(row)

print(f"cTrader trades: {len(ctrader_trades)}")
for i, trade in enumerate(ctrader_trades[:5], 1):
    print(f"  {i}. {trade.get('Symbol')} {trade.get('Mode')} {trade.get('Lots')} lots - Open: {trade.get('OpenDate')} @ {trade.get('OpenPrice')} - Close: {trade.get('CloseDate')} @ {trade.get('ClosePrice')} - P&L: {trade.get('NetProfit')}")

if len(ctrader_trades) > 5:
    print(f"  ... and {len(ctrader_trades) - 5} more trades")
print()

# Check if Python log exists and compare
if python_csv and os.path.exists(python_csv):
    python_trades = []
    with open(python_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('Number'):  # Skip empty rows
                python_trades.append(row)
    
    print(f"Python trades: {len(python_trades)}")
    for i, trade in enumerate(python_trades[:5], 1):
        print(f"  {i}. {trade.get('Symbol')} {trade.get('Mode')} {trade.get('Lots')} lots - Open: {trade.get('OpenDate')} @ {trade.get('OpenPrice')} - Close: {trade.get('CloseDate')} @ {trade.get('ClosePrice')} - P&L: {trade.get('NetProfit')}")
    
    if len(python_trades) > 5:
        print(f"  ... and {len(python_trades) - 5} more trades")
    print()
    
    # Compare
    if len(ctrader_trades) == len(python_trades):
        print("[OK] Trade count matches!")
        mismatches = []
        for i, (c, p) in enumerate(zip(ctrader_trades, python_trades), 1):
            if c != p:
                mismatches.append((i, c, p))
        
        if mismatches:
            print(f"[ERROR] Found {len(mismatches)} mismatches:")
            for idx, c, p in mismatches[:10]:  # Show first 10
                print(f"  Trade #{idx}:")
                for key in c.keys():
                    if c[key] != p[key]:
                        print(f"    {key}: cTrader='{c[key]}' vs Python='{p[key]}'")
        else:
            print("[OK] All trades match perfectly!")
    else:
        print(f"[ERROR] Trade count mismatch: cTrader={len(ctrader_trades)}, Python={len(python_trades)}")
else:
    print("⚠️  Python log file not found yet. Waiting for Python backtest to complete...")

