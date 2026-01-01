"""
Compare Kanga2 log results from C# and Python
"""
import csv
import os
from pathlib import Path

log_dir = r"C:\Users\HMz\Documents\cAlgo\Logfiles"

def get_latest_log_file(log_dir, prefix):
    """Find the latest log file with the given prefix"""
    latest_file = None
    latest_time = 0
    for f in os.listdir(log_dir):
        if f.startswith(prefix) and f.endswith(".csv"):
            f_path = os.path.join(log_dir, f)
            f_time = os.path.getmtime(f_path)
            if f_time > latest_time:
                latest_time = f_time
                latest_file = f_path
    return latest_file

def load_log(filepath):
    """Load a Kanga2 log file"""
    if not os.path.exists(filepath):
        return None
    
    trades = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Create a key from trade identifier fields
            # Use Symbol, OpenDate, OpenPrice, Lots as unique identifier
            key = f"{row.get('Symbol', '')}_{row.get('OpenDate', '')}_{row.get('OpenPrice', '')}_{row.get('Lots', '')}"
            trades.append({
                'key': key,
                'row': row
            })
    return trades

# Find latest C# and Python logs
# C# logs have format "Kanga2 _N.csv" (with space and underscore)
# Python logs should have "_Python" suffix, but may also use "Kanga2 _N.csv" format
# Strategy: Find the most recent "Kanga2 _N.csv" files and compare timestamps
# The one with "_Python" in name is Python, otherwise assume C# if older

cs_log = None
py_log = None

# Get all Kanga2 log files
all_logs = []
for f in os.listdir(log_dir):
    if f.startswith("Kanga2") and f.endswith(".csv"):
        f_path = os.path.join(log_dir, f)
        f_time = os.path.getmtime(f_path)
        all_logs.append((f_path, f_time, f))

# Sort by modification time (newest first)
all_logs.sort(key=lambda x: x[1], reverse=True)

# Find Python log (has "_Python" in name or is most recent if no suffix)
for f_path, f_time, f_name in all_logs:
    if "_Python" in f_name or "Python" in f_name:
        py_log = f_path
        break

# If no Python log found, use the most recent one as Python (assuming it's from our test)
if not py_log and all_logs:
    py_log = all_logs[0][0]

# Find C# log (second most recent, or one without Python suffix)
for f_path, f_time, f_name in all_logs:
    if f_path != py_log and ("_Python" not in f_name and "Python" not in f_name):
        cs_log = f_path
        break

# If still no C# log, use second most recent
if not cs_log and len(all_logs) > 1:
    cs_log = all_logs[1][0]
elif not cs_log and all_logs:
    # Only one log file - assume it's C# and Python is missing
    cs_log = all_logs[0][0]

print("Comparing Kanga2 Log Results")
print("=" * 80)
print(f"C# Log:   {cs_log}")
print(f"Python Log: {py_log}")
print()

if not cs_log or not py_log:
    print("Error: Could not find one or both log files.")
    exit(1)

cs_trades = load_log(cs_log)
py_trades = load_log(py_log)

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
        print(f"  {key} - {field}: C#={cs_val} vs Python={py_val} (diff: {abs(cs_val-py_val) if isinstance(cs_val, (int, float)) else 'N/A'})")
    if len(mismatches) > 20:
        print(f"  ... and {len(mismatches) - 20} more mismatches")
else:
    print("[OK] All common trades match perfectly!")

print()
print("=" * 80)

if len(cs_only) > 0:
    print(f"\nTrades only in C# ({len(cs_only)}):")
    for key in sorted(list(cs_only))[:5]:
        print(f"  {key}")
    if len(cs_only) > 5:
        print(f"  ... and {len(cs_only) - 5} more")

if len(py_only) > 0:
    print(f"\nTrades only in Python ({len(py_only)}):")
    for key in sorted(list(py_only))[:5]:
        print(f"  {key}")
    if len(py_only) > 5:
        print(f"  ... and {len(py_only) - 5} more")

