"""
Compare multiple indicator outputs between C# (cTrader) and Python (KitaTrader)
"""
import math
import os

def parse_csharp_log(filepath):
    """Parse C# multi-indicator log file"""
    data = {}
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found")
        return data
        
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if '| Info |' in line and ',' in line:
                parts = line.split('| Info |')
                if len(parts) >= 2:
                    data_part = parts[1].strip()
                    values = data_part.split(',')
                    if len(values) >= 10:
                        date = values[0]
                        time = values[1]
                        
                        try:
                            # Values: Close, EMA, RSI, BB, Vidya, MACD, Signal, Hist
                            vals = [float(v) for v in values[2:10]]
                            key = f"{date} {time}"
                            data[key] = vals
                        except ValueError:
                            continue
    return data

def parse_python_log(filepath):
    """Parse Python multi-indicator CSV log file"""
    data = {}
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found")
        return data

    with open(filepath, 'r', encoding='utf-8') as f:
        header = next(f)  # Skip header
        columns = header.strip().split(',')
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(',')
            if len(parts) >= 10:
                date, time = parts[0], parts[1]
                try:
                    vals = []
                    for v in parts[2:10]:
                        if v == "NaN":
                            vals.append(float('nan'))
                        else:
                            vals.append(float(v))
                    
                    key = f"{date} {time}"
                    data[key] = vals
                except ValueError:
                    continue
    return data

# Load data
c_path = r"C:\Users\HMz\Documents\cAlgo\Logfiles\MultiIndicator_Test_CSharp.txt"
p_path = r"C:\Users\HMz\Documents\cAlgo\Logfiles\MultiIndicator_Test_Python.csv"

c_data = parse_csharp_log(c_path)
p_data = parse_python_log(p_path)

print(f"C# Data Points: {len(c_data)}")
print(f"Python Data Points: {len(p_data)}")
print()

# Find common timestamps
common_keys = sorted(set(c_data.keys()) & set(p_data.keys()))
print(f"Common timestamps: {len(common_keys)}")
print()

if not common_keys:
    print("No common data to compare.")
    exit()

# Comparison mapping
names = ["Close", "EMA", "RSI", "BB", "Vidya", "MACD", "Signal", "Hist"]
tolerance = 0.00005  # Slight tolerance for floating point differences

mismatches = {name: [] for name in names}

for key in common_keys:
    c_vals = c_data[key]
    p_vals = p_data[key]
    
    for i in range(len(names)):
        c_v = c_vals[i]
        p_v = p_vals[i]
        
        match = False
        if math.isnan(c_v) and math.isnan(p_v):
            match = True
        elif not math.isnan(c_v) and not math.isnan(p_v):
            match = abs(c_v - p_v) < tolerance
            
        if not match:
            mismatches[names[i]].append((key, c_v, p_v))

# Summary
print("="*80)
print(f"{'Indicator':<15} | {'Mismatches':<10} | {'Status'}")
print("-"*80)

total_mismatches = 0
for name in names:
    count = len(mismatches[name])
    total_mismatches += count
    status = "PASS" if count == 0 else f"FAIL ({count})"
    print(f"{name:<15} | {count:<10} | {status}")

print("="*80)

if total_mismatches > 0:
    print("\nDetailed Mismatches (First 5 for each):")
    for name in names:
        if mismatches[name]:
            print(f"\n[{name}]")
            for key, c_v, p_v in mismatches[name][:5]:
                print(f"  {key}: C# {c_v:.6f} != Py {p_v:.6f} (diff: {abs(c_v-p_v):.6f})")
    
    print("\nDetailed Mismatches (LAST 5 for each):")
    for name in names:
        if mismatches[name]:
            print(f"\n[{name}]")
            for key, c_v, p_v in mismatches[name][-5:]:
                print(f"  {key}: C# {c_v:.6f} != Py {p_v:.6f} (diff: {abs(c_v-p_v):.6f})")
else:
    print("\nSUCCESS: All indicators match perfectly!")
