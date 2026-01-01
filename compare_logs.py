def parse_csharp_log(filepath):
    data = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            # Match line like: 
            # 22.07.2025 00:00:00.846 | Info | 2025.07.22 00:00,1.09353,1.09360,1.09320,1.09355,100.00
            if "| Info |" in line:
                parts = line.strip().split("| Info |")
                if len(parts) > 1:
                    content = parts[1].strip()
                    csv_parts = content.split(',')
                    
                    # 2025.07.22 00:00,1,09355,1,09432,1,09345,1,09357,4679,00
                    # Length should be 1 + 2*5 = 11 parts
                    if len(csv_parts) >= 11:
                         key = csv_parts[0]
                         o = float(csv_parts[1] + "." + csv_parts[2])
                         h = float(csv_parts[3] + "." + csv_parts[4])
                         l = float(csv_parts[5] + "." + csv_parts[6])
                         c = float(csv_parts[7] + "." + csv_parts[8])
                         v = float(csv_parts[9] + "." + csv_parts[10]) # Volume might use comma too? Yes "4679,00"
                         data[key] = (o, h, l, c, v)
                    elif len(csv_parts) >= 6:
                        # Fallback for dot decimals
                        key = csv_parts[0]
                        o = float(csv_parts[1])
                        h = float(csv_parts[2])
                        l = float(csv_parts[3])
                        c = float(csv_parts[4])
                        v = float(csv_parts[5])
                        data[key] = (o, h, l, c, v)
    return data

def parse_python_log(filepath):
    data = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        header = next(f) # Skip header
        for line in f:
            # 2025.07.22 00:00,O,H,L,C,V
            parts = line.strip().split(',')
            if len(parts) >= 6:
                key = parts[0]
                o = float(parts[1])
                h = float(parts[2])
                l = float(parts[3])
                c = float(parts[4])
                v = float(parts[5])
                data[key] = (o, h, l, c, v)
    return data

c_data = parse_csharp_log(r"C:\Users\HMz\Documents\cAlgo\Logfiles\PriceVerify_CSharp_Winter_D1.txt")
p_data = parse_python_log(r"C:\Users\HMz\Documents\cAlgo\Logfiles\PriceVerify_Python_Winter_D1.csv")

print(f"C# Data Points: {len(c_data)}")
print(f"Python Data Points: {len(p_data)}")

# Compare
keys = sorted(set(list(c_data.keys()) + list(p_data.keys())))
diffs = 0
for k in keys:
    if k not in c_data:
        print(f"Missing in C#: {k}")
        diffs += 1
        continue
    if k not in p_data:
        print(f"Missing in Python: {k}")
        diffs += 1
        continue
        
    co, ch, cl, cc, cv = c_data[k]
    po, ph, pl, pc, pv = p_data[k]
    
    # tolerance
    # OHLC should be close matching digits
    # Volume might differ slightly if ticks are grouped differently, but should match for H1
    if (abs(co - po) > 0.00001 or 
        abs(ch - ph) > 0.00001 or 
        abs(cl - pl) > 0.00001 or 
        abs(cc - pc) > 0.00001 or 
        abs(cv - pv) > 0.01):
        print(f"Mismatch {k}: C# {co}/{ch}/{cl}/{cc}/{cv} != Py {po}/{ph}/{pl}/{pc}/{pv}")
        diffs += 1

if diffs == 0:
    print("SUCCESS: OHLCV Logs are identical!")
else:
    print(f"FAILED: Found {diffs} differences.")
