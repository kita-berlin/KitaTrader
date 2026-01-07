"""
Compare ALL bar prices and volumes between C# and Python logs
"""
import os

def parse_final_bar(line):
    """Parse FINAL_BAR line into components"""
    if 'FINAL_BAR|' in line:
        idx = line.find('FINAL_BAR|')
        final_line = line[idx:]
        parts = final_line.split('|')
        if len(parts) >= 8:
            return {
                'tf': parts[1],
                'time': parts[2],
                'open': float(parts[3]),
                'high': float(parts[4]),
                'low': float(parts[5]),
                'close': float(parts[6]),
                'volume': int(parts[7])
            }
    return None

def main():
    cs_log_path = r'C:\Users\HMz\Documents\cAlgo\Data\cBots\OHLCTestBot\29639f65-52c0-4443-a8c7-b6511867444a\Backtesting\log.txt'
    py_log_path = r'C:\Users\HMz\Documents\cAlgo\Logfiles\OHLCTestBot_Python.log'
    
    # Read and parse both logs
    cs_bars = {}
    py_bars = {}
    
    print("Reading C# log...")
    with open(cs_log_path, 'r', encoding='utf-8') as f:
        for line in f:
            bar = parse_final_bar(line)
            if bar:
                key = f"{bar['tf']}|{bar['time']}"
                cs_bars[key] = bar
    
    print("Reading Python log...")
    with open(py_log_path, 'r', encoding='utf-8') as f:
        for line in f:
            bar = parse_final_bar(line)
            if bar:
                key = f"{bar['tf']}|{bar['time']}"
                py_bars[key] = bar
    
    print(f"\nC# bars: {len(cs_bars)}")
    print(f"Python bars: {len(py_bars)}")
    print()
    
    # Compare
    all_keys = set(cs_bars.keys()) | set(py_bars.keys())
    mismatches = []
    missing_in_py = []
    missing_in_cs = []
    
    print("Comparing all bars...")
    for key in sorted(all_keys):
        cs_bar = cs_bars.get(key)
        py_bar = py_bars.get(key)
        
        if not cs_bar:
            missing_in_cs.append(key)
            continue
        if not py_bar:
            missing_in_py.append(key)
            continue
        
        # Compare all fields with exact match
        if (cs_bar['open'] != py_bar['open'] or
            cs_bar['high'] != py_bar['high'] or
            cs_bar['low'] != py_bar['low'] or
            cs_bar['close'] != py_bar['close'] or
            cs_bar['volume'] != py_bar['volume']):
            mismatches.append({
                'key': key,
                'cs': cs_bar,
                'py': py_bar
            })
    
    print(f"\n=== COMPARISON RESULTS ===")
    print(f"Total bars to compare: {len(all_keys)}")
    print(f"Bars in both logs: {len(set(cs_bars.keys()) & set(py_bars.keys()))}")
    print(f"Mismatches: {len(mismatches)}")
    print(f"Missing in Python: {len(missing_in_py)}")
    print(f"Missing in C#: {len(missing_in_cs)}")
    print()
    
    # Breakdown by timeframe
    print("=== Breakdown by Timeframe ===")
    for tf in ['M1', 'M5', 'H1', 'H4']:
        tf_cs = {k: v for k, v in cs_bars.items() if k.startswith(f'{tf}|')}
        tf_py = {k: v for k, v in py_bars.items() if k.startswith(f'{tf}|')}
        tf_common = set(tf_cs.keys()) & set(tf_py.keys())
        tf_mismatches = [m for m in mismatches if m['key'].startswith(f'{tf}|')]
        print(f"{tf}: CS={len(tf_cs)}, PY={len(tf_py)}, Common={len(tf_common)}, Mismatches={len(tf_mismatches)}")
    print()
    
    if mismatches:
        print(f"=== FIRST 30 MISMATCHES ===")
        for i, m in enumerate(mismatches[:30], 1):
            print(f"{i}. {m['key']}")
            print(f"   C#:   O={m['cs']['open']:.5f} H={m['cs']['high']:.5f} L={m['cs']['low']:.5f} C={m['cs']['close']:.5f} V={m['cs']['volume']}")
            print(f"   Python: O={m['py']['open']:.5f} H={m['py']['high']:.5f} L={m['py']['low']:.5f} C={m['py']['close']:.5f} V={m['py']['volume']}")
            # Show which fields differ
            diffs = []
            if m['cs']['open'] != m['py']['open']:
                diffs.append(f"Open: {m['cs']['open']:.5f} vs {m['py']['open']:.5f}")
            if m['cs']['high'] != m['py']['high']:
                diffs.append(f"High: {m['cs']['high']:.5f} vs {m['py']['high']:.5f}")
            if m['cs']['low'] != m['py']['low']:
                diffs.append(f"Low: {m['cs']['low']:.5f} vs {m['py']['low']:.5f}")
            if m['cs']['close'] != m['py']['close']:
                diffs.append(f"Close: {m['cs']['close']:.5f} vs {m['py']['close']:.5f}")
            if m['cs']['volume'] != m['py']['volume']:
                diffs.append(f"Volume: {m['cs']['volume']} vs {m['py']['volume']}")
            if diffs:
                print(f"   Differences: {', '.join(diffs)}")
            print()
        
        if len(mismatches) > 30:
            print(f"... and {len(mismatches) - 30} more mismatches")
    else:
        print("[OK] ALL BARS MATCH PERFECTLY!")
        print()
        print("All prices (Open, High, Low, Close) and Volumes are identical!")
    
    if missing_in_py:
        print(f"\n=== BARS MISSING IN PYTHON ({len(missing_in_py)}) ===")
        for key in sorted(missing_in_py)[:20]:
            print(f"  {key}")
        if len(missing_in_py) > 20:
            print(f"  ... and {len(missing_in_py) - 20} more")
    
    if missing_in_cs:
        print(f"\n=== BARS MISSING IN C# ({len(missing_in_cs)}) ===")
        for key in sorted(missing_in_cs)[:20]:
            print(f"  {key}")
        if len(missing_in_cs) > 20:
            print(f"  ... and {len(missing_in_cs) - 20} more")

if __name__ == "__main__":
    main()
