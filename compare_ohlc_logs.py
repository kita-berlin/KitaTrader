"""
Compare OHLC test logs between C# and Python
Extracts FINAL_BAR entries and compares OHLC values
"""
import re
from datetime import datetime
from collections import defaultdict

def parse_python_log(log_file):
    """Parse Python log file and extract FINAL_BAR entries"""
    bars = {}
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('FINAL_BAR|'):
                # Format: FINAL_BAR|TF|TIME|OPEN|HIGH|LOW|CLOSE|VOLUME
                parts = line.strip().split('|')
                if len(parts) >= 8:
                    tf = parts[1]
                    time_str = parts[2]
                    # Filter: Only include bars from 01.12. to 03.12. (exclude 04.12.)
                    if time_str.startswith('2025-12-04'):
                        continue  # Skip bars from 04.12.
                    
                    open_price = float(parts[3])
                    high = float(parts[4])
                    low = float(parts[5])
                    close = float(parts[6])
                    volume = int(parts[7])
                    
                    key = (tf, time_str)
                    bars[key] = {
                        'open': open_price,
                        'high': high,
                        'low': low,
                        'close': close,
                        'volume': volume
                    }
    return bars

def parse_csharp_log(log_file):
    """Parse C# log file and extract FINAL_BAR entries"""
    bars = {}
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            if 'FINAL_BAR|' in line:
                # Format: TIMESTAMP | Info | FINAL_BAR|TF|TIME|OPEN|HIGH|LOW|CLOSE|VOLUME|...
                # Extract the FINAL_BAR part
                final_bar_start = line.find('FINAL_BAR|')
                if final_bar_start >= 0:
                    final_bar_line = line[final_bar_start:].strip()
                    parts = final_bar_line.split('|')
                    if len(parts) >= 8:
                        tf = parts[1]
                        time_str = parts[2]
                        open_price = float(parts[3])
                        high = float(parts[4])
                        low = float(parts[5])
                        close = float(parts[6])
                        volume = int(parts[7])
                        
                        key = (tf, time_str)
                        bars[key] = {
                            'open': open_price,
                            'high': high,
                            'low': low,
                            'close': close,
                            'volume': volume
                        }
    return bars

def compare_bars(python_bars, csharp_bars, tolerance=0.00001):
    """Compare bars from Python and C# logs"""
    # Find common keys (same timeframe and time)
    common_keys = set(python_bars.keys()) & set(csharp_bars.keys())
    python_only = set(python_bars.keys()) - set(csharp_bars.keys())
    csharp_only = set(csharp_bars.keys()) - set(python_bars.keys())
    
    matches = []
    mismatches = []
    
    for key in sorted(common_keys):
        tf, time_str = key
        py_bar = python_bars[key]
        cs_bar = csharp_bars[key]
        
        # Compare values
        diff_open = abs(py_bar['open'] - cs_bar['open'])
        diff_high = abs(py_bar['high'] - cs_bar['high'])
        diff_low = abs(py_bar['low'] - cs_bar['low'])
        diff_close = abs(py_bar['close'] - cs_bar['close'])
        diff_volume = abs(py_bar['volume'] - cs_bar['volume'])
        
        max_diff = max(diff_open, diff_high, diff_low, diff_close)
        
        if max_diff <= tolerance and diff_volume == 0:
            matches.append({
                'key': key,
                'max_diff': max_diff,
                'volume_diff': diff_volume
            })
        else:
            mismatches.append({
                'key': key,
                'python': py_bar,
                'csharp': cs_bar,
                'diffs': {
                    'open': diff_open,
                    'high': diff_high,
                    'low': diff_low,
                    'close': diff_close,
                    'volume': diff_volume
                },
                'max_diff': max_diff
            })
    
    return {
        'matches': matches,
        'mismatches': mismatches,
        'python_only': python_only,
        'csharp_only': csharp_only,
        'total_common': len(common_keys),
        'total_python': len(python_bars),
        'total_csharp': len(csharp_bars)
    }

def main():
    python_log = r"C:\Users\HMz\Documents\cAlgo\Logfiles\OHLCTestBot_Python.log"
    csharp_log = r"C:\Users\HMz\Documents\cAlgo\Data\cBots\OHLCTestBot\29639f65-52c0-4443-a8c7-b6511867444a\Backtesting\log.txt"
    
    print("=== OHLC LOG COMPARISON ===")
    print(f"Python Log: {python_log}")
    print(f"C# Log: {csharp_log}")
    print()
    
    print("Parsing Python log...")
    python_bars = parse_python_log(python_log)
    print(f"  Found {len(python_bars)} bars")
    
    print("Parsing C# log...")
    csharp_bars = parse_csharp_log(csharp_log)
    print(f"  Found {len(csharp_bars)} bars")
    print()
    
    print("Comparing bars...")
    results = compare_bars(python_bars, csharp_bars)
    
    print(f"=== COMPARISON RESULTS ===")
    print(f"Total Python bars: {results['total_python']}")
    print(f"Total C# bars: {results['total_csharp']}")
    print(f"Common bars: {results['total_common']}")
    print(f"Python-only bars: {len(results['python_only'])}")
    print(f"C#-only bars: {len(results['csharp_only'])}")
    print(f"Matches: {len(results['matches'])}")
    print(f"Mismatches: {len(results['mismatches'])}")
    print()
    
    if results['mismatches']:
        print("=== MISMATCHES ===")
        for i, mm in enumerate(results['mismatches'][:20], 1):
            tf, time_str = mm['key']
            print(f"\n{i}. {tf} @ {time_str}")
            print(f"   Python: O={mm['python']['open']:.5f} H={mm['python']['high']:.5f} L={mm['python']['low']:.5f} C={mm['python']['close']:.5f} V={mm['python']['volume']}")
            print(f"   C#:     O={mm['csharp']['open']:.5f} H={mm['csharp']['high']:.5f} L={mm['csharp']['low']:.5f} C={mm['csharp']['close']:.5f} V={mm['csharp']['volume']}")
            print(f"   Diffs:  O={mm['diffs']['open']:.8f} H={mm['diffs']['high']:.8f} L={mm['diffs']['low']:.8f} C={mm['diffs']['close']:.8f} V={mm['diffs']['volume']}")
            print(f"   Max diff: {mm['max_diff']:.8f}")
        
        if len(results['mismatches']) > 20:
            print(f"\n... and {len(results['mismatches']) - 20} more mismatches")
    
    if results['python_only']:
        print(f"\n=== PYTHON-ONLY BARS ({len(results['python_only'])}) ===")
        for key in sorted(results['python_only'])[:10]:
            print(f"  {key[0]} @ {key[1]}")
        if len(results['python_only']) > 10:
            print(f"  ... and {len(results['python_only']) - 10} more")
    
    if results['csharp_only']:
        print(f"\n=== C#-ONLY BARS ({len(results['csharp_only'])}) ===")
        for key in sorted(results['csharp_only'])[:10]:
            print(f"  {key[0]} @ {key[1]}")
        if len(results['csharp_only']) > 10:
            print(f"  ... and {len(results['csharp_only']) - 10} more")
    
    # Summary by timeframe
    print("\n=== SUMMARY BY TIMEFRAME ===")
    for tf in ['M1', 'M5', 'H1', 'H4']:
        tf_python = [k for k in python_bars.keys() if k[0] == tf]
        tf_csharp = [k for k in csharp_bars.keys() if k[0] == tf]
        tf_common = [k for k in results['matches'] if k['key'][0] == tf]
        tf_mismatches = [k for k in results['mismatches'] if k['key'][0] == tf]
        
        print(f"{tf}: Python={len(tf_python)}, C#={len(tf_csharp)}, Common={len(tf_common)}, Mismatches={len(tf_mismatches)}")
    
    # Write detailed comparison to file
    output_file = r"C:\Users\HMz\Documents\cAlgo\Logfiles\ohlc_comparison_results.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=== OHLC LOG COMPARISON RESULTS ===\n\n")
        f.write(f"Total Python bars: {results['total_python']}\n")
        f.write(f"Total C# bars: {results['total_csharp']}\n")
        f.write(f"Common bars: {results['total_common']}\n")
        f.write(f"Matches: {len(results['matches'])}\n")
        f.write(f"Mismatches: {len(results['mismatches'])}\n\n")
        
        if results['mismatches']:
            f.write("=== ALL MISMATCHES ===\n\n")
            for mm in results['mismatches']:
                tf, time_str = mm['key']
                f.write(f"{tf} @ {time_str}\n")
                f.write(f"  Python: O={mm['python']['open']:.5f} H={mm['python']['high']:.5f} L={mm['python']['low']:.5f} C={mm['python']['close']:.5f} V={mm['python']['volume']}\n")
                f.write(f"  C#:     O={mm['csharp']['open']:.5f} H={mm['csharp']['high']:.5f} L={mm['csharp']['low']:.5f} C={mm['csharp']['close']:.5f} V={mm['csharp']['volume']}\n")
                f.write(f"  Diffs:  O={mm['diffs']['open']:.8f} H={mm['diffs']['high']:.8f} L={mm['diffs']['low']:.8f} C={mm['diffs']['close']:.8f} V={mm['diffs']['volume']}\n\n")
    
    print(f"\nDetailed results written to: {output_file}")

if __name__ == "__main__":
    main()
