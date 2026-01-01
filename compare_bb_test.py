"""
Compare Bollinger Bands test results from C# and Python
"""
import csv
import os
from pathlib import Path

log_dir = r"C:\Users\HMz\Documents\cAlgo\Logfiles"

# Try different possible C# log file names
cs_file = None
for name in ["BollingerBands_Test_CS.csv", "BollingerBands_Test_CSharp.csv", "BollingerBands_Test_C#.csv"]:
    test_path = os.path.join(log_dir, name)
    if os.path.exists(test_path):
        cs_file = test_path
        break
if cs_file is None:
    cs_file = os.path.join(log_dir, "BollingerBands_Test_CS.csv")  # Default for error message
py_file = os.path.join(log_dir, "BollingerBands_Test_Python.csv")

print("Comparing Bollinger Bands Test Results")
print("=" * 80)
print(f"C# Log:   {cs_file}")
print(f"Python Log: {py_file}")
print()

# Read C# results (uses dots as decimal separators now, but CSV might have issues)
cs_data = {}
if os.path.exists(cs_file):
    with open(cs_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        # Skip header
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            # Parse CSV line manually to handle any format issues
            parts = line.split(',')
            if len(parts) >= 6:
                try:
                    date = parts[0].strip()
                    time = parts[1].strip()
                    key = f"{date} {time}"
                    # Values should already be in dot format from C# (we fixed it)
                    cs_data[key] = {
                        'Date': date,
                        'Time': time,
                        'Close': float(parts[2]),
                        'BB_Main': float(parts[3]),
                        'BB_Top': float(parts[4]),
                        'BB_Bottom': float(parts[5])
                    }
                except (ValueError, IndexError) as e:
                    # Skip malformed lines
                    continue
    print(f"C# bars: {len(cs_data)}")
else:
    print(f"ERROR: C# log file not found: {cs_file}")
    exit(1)

# Read Python results
py_data = {}
if os.path.exists(py_file):
    with open(py_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = f"{row['Date']} {row['Time']}"
            py_data[key] = {
                'Date': row['Date'],
                'Time': row['Time'],
                'Close': float(row['Close']),
                'BB_Main': float(row['BB_Main']),
                'BB_Top': float(row['BB_Top']),
                'BB_Bottom': float(row['BB_Bottom'])
            }
    print(f"Python bars: {len(py_data)}")
else:
    print(f"ERROR: Python log file not found: {py_file}")
    exit(1)

print()

# Find common timestamps
common_keys = set(cs_data.keys()) & set(py_data.keys())
cs_only = set(cs_data.keys()) - set(py_data.keys())
py_only = set(py_data.keys()) - set(cs_data.keys())

print(f"Common bars: {len(common_keys)}")
print(f"Only in C#: {len(cs_only)}")
print(f"Only in Python: {len(py_only)}")
print()

# Compare common bars
mismatches = []
tolerance = 0.00001  # Allow small floating point differences

for key in sorted(common_keys):
    cs = cs_data[key]
    py = py_data[key]
    
    if abs(cs['Close'] - py['Close']) > tolerance:
        mismatches.append((key, 'Close', cs['Close'], py['Close']))
    if abs(cs['BB_Main'] - py['BB_Main']) > tolerance:
        mismatches.append((key, 'BB_Main', cs['BB_Main'], py['BB_Main']))
    if abs(cs['BB_Top'] - py['BB_Top']) > tolerance:
        mismatches.append((key, 'BB_Top', cs['BB_Top'], py['BB_Top']))
    if abs(cs['BB_Bottom'] - py['BB_Bottom']) > tolerance:
        mismatches.append((key, 'BB_Bottom', cs['BB_Bottom'], py['BB_Bottom']))

if mismatches:
    print(f"[ERROR] Found {len(mismatches)} mismatches:")
    for key, field, cs_val, py_val in mismatches[:20]:  # Show first 20
        print(f"  {key} - {field}: C#={cs_val:.5f} vs Python={py_val:.5f} (diff: {abs(cs_val-py_val):.5f})")
    if len(mismatches) > 20:
        print(f"  ... and {len(mismatches) - 20} more mismatches")
else:
    print("[OK] All common bars match perfectly!")

print()
print("=" * 80)

if len(cs_only) > 0:
    print(f"\nBars only in C# ({len(cs_only)}):")
    for key in sorted(list(cs_only))[:5]:
        print(f"  {key}")
    if len(cs_only) > 5:
        print(f"  ... and {len(cs_only) - 5} more")

if len(py_only) > 0:
    print(f"\nBars only in Python ({len(py_only)}):")
    for key in sorted(list(py_only))[:5]:
        print(f"  {key}")
    if len(py_only) > 5:
        print(f"  ... and {len(py_only) - 5} more")

