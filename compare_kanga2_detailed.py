"""
Detailed comparison of Kanga2 log results from C# and Python
"""
import csv
import os
from pathlib import Path

log_dir = r"C:\Users\HMz\Documents\cAlgo\Logfiles"

def load_log_detailed(filepath):
    """Load a Kanga2 log file, handling sep=, header"""
    if not os.path.exists(filepath):
        return None
    
    trades = []
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
        # Skip sep=, line if present
        start_idx = 0
        if lines and lines[0].strip().startswith('sep='):
            start_idx = 1
        
        # Read CSV from the header line
        reader = csv.DictReader(lines[start_idx:])
        for row in reader:
            if not row or not any(row.values()):  # Skip empty rows
                continue
            # Skip footer lines (lines that don't start with a number in the Number column)
            number = (row.get('Number') or '').strip()
            symbol = (row.get('Symbol') or '').strip()
            # Stop reading when we hit footer lines (Number is not a digit or Symbol is empty)
            # This handles CSV files that have statistics at the end
            if not number or not number.isdigit() or not symbol:
                break  # Stop reading, we've hit the footer
            # Create a key from trade identifier fields
            # Use Number as part of key to handle duplicate trades with same open conditions
            open_date = (row.get('OpenDate') or '').strip()
            open_price = (row.get('OpenPrice') or '').strip()
            lots = (row.get('Lots') or '').strip()
            # Use Number to make key unique
            key = f"{symbol}_{open_date}_{open_price}_{lots}_{number}"
            trades.append({
                'key': key,
                'row': row
            })
    return trades

# Find latest C# and Python logs
log_dir_path = Path(log_dir)
# Find C# log (pattern: Kanga2 _N.csv)
cs_logs = sorted(log_dir_path.glob("Kanga2 _*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
# Find Python log (pattern: Kanga2*_Python.csv or Kanga2*Python.csv)
py_logs = sorted(log_dir_path.glob("Kanga2*Python*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)

cs_log = str(cs_logs[0]) if cs_logs else None
py_log = str(py_logs[0]) if py_logs else None

print("Comparing Kanga2 Log Results")
print("=" * 80)
print(f"C# Log:   {cs_log}")
print(f"Python Log: {py_log}")
print()

if not os.path.exists(cs_log) or not os.path.exists(py_log):
    print("Error: Could not find one or both log files.")
    exit(1)

cs_trades = load_log_detailed(cs_log)
py_trades = load_log_detailed(py_log)

if cs_trades is None or py_trades is None:
    print("Error: Failed to load one or both log files.")
    exit(1)

print(f"C# trades: {len(cs_trades)}")
print(f"Python trades: {len(py_trades)}")
print()

# Create dictionaries by key for comparison
cs_dict = {t['key']: t['row'] for t in cs_trades}
py_dict = {t['key']: t['row'] for t in py_trades}

common_keys = set(cs_dict.keys()) & set(py_dict.keys())
cs_only = set(cs_dict.keys()) - set(py_dict.keys())
py_only = set(py_dict.keys()) - set(cs_dict.keys())

print(f"Common trades: {len(common_keys)}")
print(f"Only in C#: {len(cs_only)}")
print(f"Only in Python: {len(py_only)}")
print()

# Compare common trades
mismatches = []
tolerance = 0.00001

for key in sorted(common_keys):
    cs = cs_dict[key]
    py = py_dict[key]
    
    # Compare relevant columns
    for col in ['NetProfit', 'OpenPrice', 'ClosePrice', 'BollingerUpper', 'BollingerLower', 'BollingerMain', 'Lots']:
        if col in cs and col in py:
            try:
                cs_val = float(cs[col]) if cs[col] else 0.0
                py_val = float(py[col]) if py[col] else 0.0
                if abs(cs_val - py_val) > tolerance:
                    mismatches.append((key, col, cs_val, py_val))
            except (ValueError, TypeError):
                if cs[col] != py[col]:
                    mismatches.append((key, col, cs[col], py[col]))

if mismatches:
    print(f"[ERROR] Found {len(mismatches)} mismatches:")
    for key, field, cs_val, py_val in mismatches[:20]:  # Show first 20
        diff = abs(cs_val-py_val) if isinstance(cs_val, (int, float)) and isinstance(py_val, (int, float)) else 'N/A'
        print(f"  {key} - {field}: C#={cs_val} vs Python={py_val} (diff: {diff})")
    if len(mismatches) > 20:
        print(f"  ... and {len(mismatches) - 20} more mismatches")
else:
    print("[OK] All common trades match perfectly!")

print()
print("=" * 80)

if len(cs_only) > 0:
    print(f"\nTrades only in C# ({len(cs_only)}):")
    for key in sorted(list(cs_only))[:10]:
        cs = cs_dict[key]
        print(f"  {key} - {cs.get('OpenDate', 'N/A')} - NetProfit: {cs.get('NetProfit', 'N/A')}")
    if len(cs_only) > 10:
        print(f"  ... and {len(cs_only) - 10} more")

if len(py_only) > 0:
    print(f"\nTrades only in Python ({len(py_only)}):")
    for key in sorted(list(py_only))[:10]:
        py = py_dict[key]
        print(f"  {key} - {py.get('OpenDate', 'N/A')} - NetProfit: {py.get('NetProfit', 'N/A')}")
    if len(py_only) > 10:
        print(f"  ... and {len(py_only) - 10} more")

# Summary statistics
if len(common_keys) > 0:
    print("\n" + "=" * 80)
    print("Summary Statistics for Common Trades:")
    cs_total_profit = sum(float(cs_dict[k].get('NetProfit', 0) or 0) for k in common_keys)
    py_total_profit = sum(float(py_dict[k].get('NetProfit', 0) or 0) for k in common_keys)
    print(f"Total Net Profit - C#: {cs_total_profit:.2f}, Python: {py_total_profit:.2f}, Diff: {abs(cs_total_profit - py_total_profit):.2f}")

# Show sample of keys to understand matching issue
if len(common_keys) < len(cs_trades) or len(common_keys) < len(py_trades):
    print("\n" + "=" * 80)
    print("Sample Keys (first 5 from each):")
    print("C# keys:")
    for i, key in enumerate(sorted(cs_dict.keys())[:5]):
        print(f"  {i+1}. {key}")
    print("Python keys:")
    for i, key in enumerate(sorted(py_dict.keys())[:5]):
        print(f"  {i+1}. {key}")

