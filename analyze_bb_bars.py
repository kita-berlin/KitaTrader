import csv
import os

cs_file = r"C:\Users\HMz\Documents\cAlgo\Logfiles\BollingerBands_Test_CS.csv"
py_file = r"C:\Users\HMz\Documents\cAlgo\Logfiles\BollingerBands_Test_Python.csv"

def load_bars(filepath):
    bars = []
    with open(filepath, 'r', encoding='utf-8-sig') as f:  # utf-8-sig handles BOM
        lines = f.readlines()
    # Skip sep= line and header
    start_idx = 1 if lines[0].strip().startswith('sep=') else 0
    for line in lines[start_idx + 1:]:  # Skip header line
        line = line.strip()
        if not line:
            continue
        parts = line.split(',')
        if len(parts) >= 2:
            date = parts[0].strip()
            time = parts[1].strip()
            if date and time and date != 'Date':
                bars.append(f"{date} {time}")
    return bars

cs_bars = load_bars(cs_file)
py_bars = load_bars(py_file)

print("=" * 60)
print("Bar Range Analysis")
print("=" * 60)
print(f"\nC# bars: {len(cs_bars)}")
print(f"Python bars: {len(py_bars)}")
print(f"\nC# first 5 bars:")
for bar in cs_bars[:5]:
    print(f"  {bar}")
print(f"\nC# last 5 bars:")
for bar in cs_bars[-5:]:
    print(f"  {bar}")
print(f"\nPython first 5 bars:")
for bar in py_bars[:5]:
    print(f"  {bar}")
print(f"\nPython last 5 bars:")
for bar in py_bars[-5:]:
    print(f"  {bar}")

# Find bars only in C#
cs_set = set(cs_bars)
py_set = set(py_bars)
only_cs = sorted(list(cs_set - py_set))
print(f"\nBars only in C# ({len(only_cs)}):")
print("  First 10:")
for bar in only_cs[:10]:
    print(f"    {bar}")
if len(only_cs) > 10:
    print(f"  ... and {len(only_cs) - 10} more")
    print("  Last 5:")
    for bar in only_cs[-5:]:
        print(f"    {bar}")

