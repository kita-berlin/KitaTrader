"""
Compare EMA output between C# (cTrader) and Python (KitaTrader)
"""

def parse_csharp_ema_log(filepath):
    """Parse C# EMA log file"""
    data = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if '| Info |' in line and ':00,' in line:
                parts = line.split('| Info |')
                if len(parts) >= 2:
                    data_part = parts[1].strip()
                    values = data_part.split(',')
                    if len(values) >= 6:  # Fixed: was checking len(parts)
                        date = values[0]
                        time = values[1]
                        close = float(f"{values[2]}.{values[3]}")
                        ema = float(f"{values[4]}.{values[5]}")
                        
                        key = f"{date} {time}"
                        data[key] = (close, ema)
    return data

def parse_python_ema_log(filepath):
    """Parse Python EMA CSV log file"""
    data = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        next(f)  # Skip header
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(',')
            if len(parts) >= 4:
                date, time, close, ema = parts[:4]
                close = float(close)
                ema = float(ema)
                
                key = f"{date} {time}"
                data[key] = (close, ema)
    return data

# Load data
c_data = parse_csharp_ema_log(r"C:\Users\HMz\Documents\cAlgo\Logfiles\EMA_Test_CSharp.txt")
p_data = parse_python_ema_log(r"C:\Users\HMz\Documents\cAlgo\Logfiles\EMA_Test_Python.csv")

print(f"C# Data Points: {len(c_data)}")
print(f"Python Data Points: {len(p_data)}")
print()

# Find common timestamps
common_keys = set(c_data.keys()) & set(p_data.keys())
print(f"Common timestamps: {len(common_keys)}")
print()

# Compare values
mismatches = []
tolerance = 0.00001  # 5 decimal places

for key in sorted(common_keys):
    c_close, c_ema = c_data[key]
    p_close, p_ema = p_data[key]
    
    close_match = abs(c_close - p_close) < tolerance
    ema_match = abs(c_ema - p_ema) < tolerance
    
    if not (close_match and ema_match):
        mismatches.append({
            'time': key,
            'c': (c_close, c_ema),
            'p': (p_close, p_ema)
        })
        print(f"Mismatch {key}:")
        if not close_match:
            print(f"  Close: C# {c_close:.5f} != Py {p_close:.5f}")
        if not ema_match:
            print(f"  EMA: C# {c_ema:.5f} != Py {p_ema:.5f} (diff: {abs(c_ema - p_ema):.8f})")
    else:
        print(f"✅ {key}: Close={c_close:.5f}, EMA={c_ema:.5f}")

# Report missing data
c_only = set(c_data.keys()) - set(p_data.keys())
p_only = set(p_data.keys()) - set(c_data.keys())

if c_only:
    print(f"\n{len(c_only)} timestamps only in C#:")
    for key in sorted(c_only)[:5]:
        c_close, c_ema = c_data[key]
        print(f"  {key}: Close={c_close:.5f}, EMA={c_ema:.5f}")
    if len(c_only) > 5:
        print(f"  ... and {len(c_only) - 5} more")

if p_only:
    print(f"\n{len(p_only)} timestamps only in Python:")
    for key in sorted(p_only)[:5]:
        p_close, p_ema = p_data[key]
        print(f"  {key}: Close={p_close:.5f}, EMA={p_ema:.5f}")
    if len(p_only) > 5:
        print(f"  ... and {len(p_only) - 5} more")

# Final result
print("\n" + "="*80)
if len(mismatches) == 0 and len(common_keys) > 0:
    print("SUCCESS: All EMA values match perfectly!")
elif len(common_keys) == 0:
    print("WARNING: No common timestamps found between C# and Python outputs.")
else:
    print(f"FAILED: Found {len(mismatches)} mismatches out of {len(common_keys)} common timestamps.")
print("="*80)
