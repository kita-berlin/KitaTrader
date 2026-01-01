"""
Compare Bollinger Bands output between C# (cTrader) and Python (KitaTrader)
"""

def parse_csharp_bb_log(filepath):
    """Parse C# Bollinger Bands log file"""
    data = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            # Match lines like: "10.07.2025 01:00:00.226 | Info | 2025.07.10,00:00,1,08951,1,08933,1,09052,1,08813"
            if '| Info |' in line and ',00:00,' in line or ',01:00,' in line or ',02:00,' in line or ':00,' in line:
                parts = line.split('| Info |')
                if len(parts) >= 2:
                    data_part = parts[1].strip()
                    # Split by comma and reconstruct decimals
                    # Format: Date,Time,Int,Dec,Int,Dec,Int,Dec,Int,Dec
                    values = data_part.split(',')
                    if len(values) >= 10:
                        date = values[0]  # 2025.07.10
                        time = values[1]  # 00:00
                        close = float(f"{values[2]}.{values[3]}")  # 1.08951
                        bb_main = float(f"{values[4]}.{values[5]}")  # 1.08933
                        bb_top = float(f"{values[6]}.{values[7]}")  # 1.09052
                        bb_bottom = float(f"{values[8]}.{values[9]}")  # 1.08813
                        
                        key = f"{date} {time}"
                        data[key] = (close, bb_main, bb_top, bb_bottom)
    return data

def parse_python_bb_log(filepath):
    """Parse Python Bollinger Bands CSV log file"""
    data = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        next(f)  # Skip header
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Format: Date,Time,Close,BB_Main,BB_Top,BB_Bottom
            parts = line.split(',')
            if len(parts) >= 6:
                date, time, close, bb_main, bb_top, bb_bottom = parts[:6]
                close = float(close)
                bb_main = float(bb_main)
                bb_top = float(bb_top)
                bb_bottom = float(bb_bottom)
                
                key = f"{date} {time}"
                data[key] = (close, bb_main, bb_top, bb_bottom)
    return data

# Load data
c_data = parse_csharp_bb_log(r"C:\Users\HMz\Documents\cAlgo\Logfiles\BollingerBands_Test_CSharp.txt")
p_data = parse_python_bb_log(r"C:\Users\HMz\Documents\cAlgo\Logfiles\BollingerBands_Test_Python.csv")

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
    c_close, c_main, c_top, c_bottom = c_data[key]
    p_close, p_main, p_top, p_bottom = p_data[key]
    
    close_match = abs(c_close - p_close) < tolerance
    main_match = abs(c_main - p_main) < tolerance
    top_match = abs(c_top - p_top) < tolerance
    bottom_match = abs(c_bottom - p_bottom) < tolerance
    
    if not (close_match and main_match and top_match and bottom_match):
        mismatches.append({
            'time': key,
            'c': (c_close, c_main, c_top, c_bottom),
            'p': (p_close, p_main, p_top, p_bottom)
        })
        print(f"Mismatch {key}:")
        if not close_match:
            print(f"  Close: C# {c_close:.5f} != Py {p_close:.5f}")
        if not main_match:
            print(f"  BB Main: C# {c_main:.5f} != Py {p_main:.5f}")
        if not top_match:
            print(f"  BB Top: C# {c_top:.5f} != Py {p_top:.5f}")
        if not bottom_match:
            print(f"  BB Bottom: C# {c_bottom:.5f} != Py {p_bottom:.5f}")
    else:
        print(f"✅ {key}: Close={c_close:.5f}, Main={c_main:.5f}, Top={c_top:.5f}, Bottom={c_bottom:.5f}")

# Report missing data
c_only = set(c_data.keys()) - set(p_data.keys())
p_only = set(p_data.keys()) - set(c_data.keys())

if c_only:
    print(f"\n{len(c_only)} timestamps only in C#:")
    for key in sorted(c_only)[:5]:
        c_close, c_main, c_top, c_bottom = c_data[key]
        print(f"  {key}: Close={c_close:.5f}, Main={c_main:.5f}")
    if len(c_only) > 5:
        print(f"  ... and {len(c_only) - 5} more")

if p_only:
    print(f"\n{len(p_only)} timestamps only in Python:")
    for key in sorted(p_only)[:5]:
        p_close, p_main, p_top, p_bottom = p_data[key]
        print(f"  {key}: Close={p_close:.5f}, Main={p_main:.5f}")
    if len(p_only) > 5:
        print(f"  ... and {len(p_only) - 5} more")

# Final result
print("\n" + "="*80)
if len(mismatches) == 0 and len(common_keys) > 0:
    print("SUCCESS: All Bollinger Bands values match perfectly!")
elif len(common_keys) == 0:
    print("WARNING: No common timestamps found between C# and Python outputs.")
else:
    print(f"FAILED: Found {len(mismatches)} mismatches out of {len(common_keys)} common timestamps.")
print("="*80)
