"""
Compare RSI internal EMA values (gains/losses) between C# and Python
This script helps debug RSI differences by checking if the internal EMAs match
"""
import re
from datetime import datetime

def extract_rsi_values(log_file, is_python=True):
    """Extract RSI values from log file"""
    rsi_values = {}
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            if is_python and line.startswith('FINAL_IND|'):
                parts = line.strip().split('|')
                if len(parts) >= 4:
                    tf = parts[1]
                    time_str = parts[2]
                    if time_str.startswith('2025-12-04'):
                        continue
                    for part in parts[3:]:
                        if part.startswith('RSI='):
                            rsi_val = float(part.split('=')[1])
                            key = (tf, time_str)
                            rsi_values[key] = rsi_val
            elif not is_python and 'FINAL_IND|' in line:
                final_ind_start = line.find('FINAL_IND|')
                if final_ind_start >= 0:
                    final_ind_line = line[final_ind_start:].strip()
                    parts = final_ind_line.split('|')
                    if len(parts) >= 4:
                        tf = parts[1]
                        time_str = parts[2]
                        for part in parts[3:]:
                            if part.startswith('RSI='):
                                rsi_val = float(part.split('=')[1])
                                key = (tf, time_str)
                                rsi_values[key] = rsi_val
    return rsi_values

def main():
    python_log = r"C:\Users\HMz\Documents\cAlgo\Logfiles\OHLCTestBot_Python.log"
    csharp_log = r"C:\Users\HMz\Documents\cAlgo\Data\cBots\OHLCTestBot\29639f65-52c0-4443-a8c7-b6511867444a\Backtesting\log.txt"
    
    print("=== RSI VALUE COMPARISON ===")
    print("Extracting RSI values...")
    
    python_rsi = extract_rsi_values(python_log, is_python=True)
    csharp_rsi = extract_rsi_values(csharp_log, is_python=False)
    
    print(f"Python RSI entries: {len(python_rsi)}")
    print(f"C# RSI entries: {len(csharp_rsi)}")
    print()
    
    # Find common keys
    common_keys = set(python_rsi.keys()) & set(csharp_rsi.keys())
    print(f"Common entries: {len(common_keys)}")
    print()
    
    # Compare RSI values
    mismatches = []
    matches = []
    
    for key in sorted(common_keys):
        py_val = python_rsi[key]
        cs_val = csharp_rsi[key]
        diff = abs(py_val - cs_val)
        
        if diff > 0.00001:
            mismatches.append({
                'key': key,
                'python': py_val,
                'csharp': cs_val,
                'diff': diff
            })
        else:
            matches.append(key)
    
    print(f"Matches: {len(matches)}")
    print(f"Mismatches: {len(mismatches)}")
    print()
    
    if mismatches:
        print("=== RSI MISMATCHES (showing first 30) ===")
        for i, mm in enumerate(mismatches[:30], 1):
            tf, time_str = mm['key']
            print(f"{i}. {tf} @ {time_str}: Py={mm['python']:.5f}, C#={mm['csharp']:.5f}, Diff={mm['diff']:.8f}")
        
        # Group by timeframe
        print("\n=== MISMATCHES BY TIMEFRAME ===")
        for tf in ['M1', 'M5', 'H1', 'H4']:
            tf_mismatches = [mm for mm in mismatches if mm['key'][0] == tf]
            if tf_mismatches:
                avg_diff = sum(mm['diff'] for mm in tf_mismatches) / len(tf_mismatches)
                max_diff = max(mm['diff'] for mm in tf_mismatches)
                print(f"{tf}: {len(tf_mismatches)} mismatches, Avg diff: {avg_diff:.8f}, Max diff: {max_diff:.8f}")

if __name__ == "__main__":
    main()
