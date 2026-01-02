"""
Compare Bollinger Bands test results from C# and Python
Now compares all OHLC values and BB indicators on all OHLC
"""
import csv
import os

log_dir = r"C:\Users\HMz\Documents\cAlgo\Logfiles"
cs_log = os.path.join(log_dir, "BollingerBands_Test_CS.csv")
py_log = os.path.join(log_dir, "BollingerBands_Test_Python.csv")

print("Comparing Bollinger Bands Test Results")
print("=" * 80)
print(f"C# Log:   {cs_log}")
print(f"Python Log: {py_log}")
print()

if not os.path.exists(cs_log):
    print(f"ERROR: C# log file not found: {cs_log}")
    exit(1)

if not os.path.exists(py_log):
    print(f"ERROR: Python log file not found: {py_log}")
    exit(1)

# Read and parse CSV files
cs_data = {}
py_data = {}

with open(cs_log, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        key = f"{row['Date']} {row['Time']}"
        cs_data[key] = {
            'open': float(row['Open']),
            'high': float(row['High']),
            'low': float(row['Low']),
            'close': float(row['Close']),
            'bb_open_main': float(row['BB_Open_Main']),
            'bb_open_top': float(row['BB_Open_Top']),
            'bb_open_bottom': float(row['BB_Open_Bottom']),
            'bb_high_main': float(row['BB_High_Main']),
            'bb_high_top': float(row['BB_High_Top']),
            'bb_high_bottom': float(row['BB_High_Bottom']),
            'bb_low_main': float(row['BB_Low_Main']),
            'bb_low_top': float(row['BB_Low_Top']),
            'bb_low_bottom': float(row['BB_Low_Bottom']),
            'bb_close_main': float(row['BB_Close_Main']),
            'bb_close_top': float(row['BB_Close_Top']),
            'bb_close_bottom': float(row['BB_Close_Bottom'])
        }

with open(py_log, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = f"{row['Date']} {row['Time']}"
            py_data[key] = {
            'open': float(row['Open']),
            'high': float(row['High']),
            'low': float(row['Low']),
            'close': float(row['Close']),
            'bb_open_main': float(row['BB_Open_Main']),
            'bb_open_top': float(row['BB_Open_Top']),
            'bb_open_bottom': float(row['BB_Open_Bottom']),
            'bb_high_main': float(row['BB_High_Main']),
            'bb_high_top': float(row['BB_High_Top']),
            'bb_high_bottom': float(row['BB_High_Bottom']),
            'bb_low_main': float(row['BB_Low_Main']),
            'bb_low_top': float(row['BB_Low_Top']),
            'bb_low_bottom': float(row['BB_Low_Bottom']),
            'bb_close_main': float(row['BB_Close_Main']),
            'bb_close_top': float(row['BB_Close_Top']),
            'bb_close_bottom': float(row['BB_Close_Bottom'])
        }

# Compare common bars
common_keys = set(cs_data.keys()) & set(py_data.keys())
only_cs = set(cs_data.keys()) - set(py_data.keys())
only_py = set(py_data.keys()) - set(cs_data.keys())

print(f"C# bars: {len(cs_data)}")
print(f"Python bars: {len(py_data)}")
print(f"\nCommon bars: {len(common_keys)}")
print(f"Only in C#: {len(only_cs)}")
print(f"Only in Python: {len(only_py)}")

if only_cs:
    print(f"\nBars only in C#: {sorted(list(only_cs))[:10]}...")
if only_py:
    print(f"\nBars only in Python: {sorted(list(only_py))[:10]}...")

# Check for differences
tolerance = 0.00001
differences = []
for key in sorted(common_keys):
    cs = cs_data[key]
    py = py_data[key]
    
    # Compare OHLC values
    if abs(cs['open'] - py['open']) > tolerance:
        differences.append(f"{key}: Open mismatch - C#: {cs['open']:.5f}, Python: {py['open']:.5f}")
    if abs(cs['high'] - py['high']) > tolerance:
        differences.append(f"{key}: High mismatch - C#: {cs['high']:.5f}, Python: {py['high']:.5f}")
    if abs(cs['low'] - py['low']) > tolerance:
        differences.append(f"{key}: Low mismatch - C#: {cs['low']:.5f}, Python: {py['low']:.5f}")
    if abs(cs['close'] - py['close']) > tolerance:
        differences.append(f"{key}: Close mismatch - C#: {cs['close']:.5f}, Python: {py['close']:.5f}")
    
    # Compare BB on Open
    if abs(cs['bb_open_main'] - py['bb_open_main']) > tolerance:
        differences.append(f"{key}: BB_Open_Main mismatch - C#: {cs['bb_open_main']:.5f}, Python: {py['bb_open_main']:.5f}")
    if abs(cs['bb_open_top'] - py['bb_open_top']) > tolerance:
        differences.append(f"{key}: BB_Open_Top mismatch - C#: {cs['bb_open_top']:.5f}, Python: {py['bb_open_top']:.5f}")
    if abs(cs['bb_open_bottom'] - py['bb_open_bottom']) > tolerance:
        differences.append(f"{key}: BB_Open_Bottom mismatch - C#: {cs['bb_open_bottom']:.5f}, Python: {py['bb_open_bottom']:.5f}")
    
    # Compare BB on High
    if abs(cs['bb_high_main'] - py['bb_high_main']) > tolerance:
        differences.append(f"{key}: BB_High_Main mismatch - C#: {cs['bb_high_main']:.5f}, Python: {py['bb_high_main']:.5f}")
    if abs(cs['bb_high_top'] - py['bb_high_top']) > tolerance:
        differences.append(f"{key}: BB_High_Top mismatch - C#: {cs['bb_high_top']:.5f}, Python: {py['bb_high_top']:.5f}")
    if abs(cs['bb_high_bottom'] - py['bb_high_bottom']) > tolerance:
        differences.append(f"{key}: BB_High_Bottom mismatch - C#: {cs['bb_high_bottom']:.5f}, Python: {py['bb_high_bottom']:.5f}")
    
    # Compare BB on Low
    if abs(cs['bb_low_main'] - py['bb_low_main']) > tolerance:
        differences.append(f"{key}: BB_Low_Main mismatch - C#: {cs['bb_low_main']:.5f}, Python: {py['bb_low_main']:.5f}")
    if abs(cs['bb_low_top'] - py['bb_low_top']) > tolerance:
        differences.append(f"{key}: BB_Low_Top mismatch - C#: {cs['bb_low_top']:.5f}, Python: {py['bb_low_top']:.5f}")
    if abs(cs['bb_low_bottom'] - py['bb_low_bottom']) > tolerance:
        differences.append(f"{key}: BB_Low_Bottom mismatch - C#: {cs['bb_low_bottom']:.5f}, Python: {py['bb_low_bottom']:.5f}")
    
    # Compare BB on Close
    if abs(cs['bb_close_main'] - py['bb_close_main']) > tolerance:
        differences.append(f"{key}: BB_Close_Main mismatch - C#: {cs['bb_close_main']:.5f}, Python: {py['bb_close_main']:.5f}")
    if abs(cs['bb_close_top'] - py['bb_close_top']) > tolerance:
        differences.append(f"{key}: BB_Close_Top mismatch - C#: {cs['bb_close_top']:.5f}, Python: {py['bb_close_top']:.5f}")
    if abs(cs['bb_close_bottom'] - py['bb_close_bottom']) > tolerance:
        differences.append(f"{key}: BB_Close_Bottom mismatch - C#: {cs['bb_close_bottom']:.5f}, Python: {py['bb_close_bottom']:.5f}")

if differences:
    print(f"\n[ERROR] Found {len(differences)} differences:")
    for diff in differences[:20]:  # Show first 20
        print(f"  {diff}")
    if len(differences) > 20:
        print(f"  ... and {len(differences) - 20} more")
else:
    print("\n[OK] All common bars match perfectly!")

print()
print("=" * 80)
