"""
Compare OHLCTestBot log files from C# and Python
Extracts FINAL_BAR lines and compares them
"""
import os
import sys
from typing import Dict, List, Tuple

def extract_final_bar_lines(log_path: str) -> Dict[str, List[str]]:
    """
    Extract FINAL_BAR lines from log file.
    Returns dict: {tf: [lines]}
    """
    if not os.path.exists(log_path):
        return {}
    
    result = {}
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                if "FINAL_BAR|" in line:
                    # Extract FINAL_BAR line (might have timestamp prefix)
                    if line.strip().startswith("FINAL_BAR|"):
                        final_line = line.strip()
                    else:
                        idx = line.find("FINAL_BAR|")
                        if idx >= 0:
                            final_line = line[idx:].strip()
                        else:
                            continue
                    
                    parts = final_line.split("|")
                    if len(parts) >= 3:
                        tf = parts[1]
                        if tf not in result:
                            result[tf] = []
                        result[tf].append(final_line)
    except Exception as e:
        print(f"Error reading {log_path}: {e}")
    
    return result

def parse_final_bar_line(line: str) -> dict:
    """Parse FINAL_BAR line into components"""
    parts = line.split("|")
    if len(parts) < 8:
        return None
    
    return {
        'tf': parts[1],
        'time': parts[2],
        'open': parts[3],
        'high': parts[4],
        'low': parts[5],
        'close': parts[6],
        'volume': parts[7],
        'indicators': parts[8:] if len(parts) > 8 else []
    }

def compare_logs(cs_log_path: str, py_log_path: str):
    """Compare C# and Python log files"""
    print(f"Comparing logs:")
    print(f"  C#: {cs_log_path}")
    print(f"  Python: {py_log_path}")
    print()
    
    cs_data = extract_final_bar_lines(cs_log_path)
    py_data = extract_final_bar_lines(py_log_path)
    
    if not cs_data and not py_data:
        print("ERROR: No FINAL_BAR lines found in either log file")
        return
    
    all_tfs = set(list(cs_data.keys()) + list(py_data.keys()))
    
    total_mismatches = 0
    total_matches = 0
    
    for tf in sorted(all_tfs):
        cs_lines = cs_data.get(tf, [])
        py_lines = py_data.get(tf, [])
        
        print(f"\n=== Timeframe: {tf} ===")
        print(f"  C# bars: {len(cs_lines)}")
        print(f"  Python bars: {len(py_lines)}")
        
        # Create lookup by time
        cs_by_time = {}
        for line in cs_lines:
            parsed = parse_final_bar_line(line)
            if parsed:
                cs_by_time[parsed['time']] = parsed
        
        py_by_time = {}
        for line in py_lines:
            parsed = parse_final_bar_line(line)
            if parsed:
                py_by_time[parsed['time']] = parsed
        
        # Compare bars that exist in both
        common_times = set(cs_by_time.keys()) & set(py_by_time.keys())
        missing_in_py = set(cs_by_time.keys()) - set(py_by_time.keys())
        missing_in_cs = set(py_by_time.keys()) - set(cs_by_time.keys())
        
        if missing_in_py:
            print(f"  WARNING: {len(missing_in_py)} bars in C# but not in Python")
        if missing_in_cs:
            print(f"  WARNING: {len(missing_in_cs)} bars in Python but not in C#")
        
        # Compare common bars
        mismatches = []
        for time in sorted(common_times):
            cs_bar = cs_by_time[time]
            py_bar = py_by_time[time]
            
            # Compare OHLCV
            bar_mismatches = []
            for field in ['open', 'high', 'low', 'close', 'volume']:
                if cs_bar[field] != py_bar[field]:
                    bar_mismatches.append(f"{field}: CS={cs_bar[field]} PY={py_bar[field]}")
            
            # Compare indicators
            cs_inds = cs_bar['indicators']
            py_inds = py_bar['indicators']
            ind_names = ['SMA', 'EMA', 'WMA', 'HMA', 'SD', 'BB_TOP', 'RSI', 'MACD']
            
            for i, ind_name in enumerate(ind_names):
                if i < len(cs_inds) and i < len(py_inds):
                    cs_val = cs_inds[i].strip()
                    py_val = py_inds[i].strip()
                    if cs_val and py_val and cs_val != py_val:
                        bar_mismatches.append(f"{ind_name}: CS={cs_val} PY={py_val}")
            
            if bar_mismatches:
                mismatches.append((time, bar_mismatches))
                total_mismatches += 1
            else:
                total_matches += 1
        
        if mismatches:
            print(f"  MISMATCHES: {len(mismatches)}")
            for time, errors in mismatches[:10]:  # Show first 10
                print(f"    {time}: {', '.join(errors)}")
            if len(mismatches) > 10:
                print(f"    ... and {len(mismatches) - 10} more")
        else:
            print(f"  [OK] All {len(common_times)} bars match!")
    
    print(f"\n=== Summary ===")
    print(f"  Total matches: {total_matches}")
    print(f"  Total mismatches: {total_mismatches}")
    if total_mismatches == 0:
        print("  [OK] PERFECT MATCH!")

if __name__ == "__main__":
    log_dir = r"C:\Users\HMz\Documents\cAlgo\Logfiles"
    
    # C# log from backtesting
    cs_log = r"C:\Users\HMz\Documents\cAlgo\Data\cBots\OHLCTestBot\29639f65-52c0-4443-a8c7-b6511867444a\Backtesting\log.txt"
    
    # Python log
    py_log = os.path.join(log_dir, "OHLCTestBot_Python.log")
    
    # Fallback paths for C# log
    if not os.path.exists(cs_log):
        cs_log = os.path.join(log_dir, "OHLCTestBot_CSharp.log")
    if not os.path.exists(cs_log):
        cs_log = os.path.join(log_dir, "OHLCTestBot.log")
    
    compare_logs(cs_log, py_log)
