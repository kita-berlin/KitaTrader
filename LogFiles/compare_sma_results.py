"""
Compare SMA indicator results between C# and Python bots
Supports OHLCV (Open, High, Low, Close, Volume) and SMA for OHLC.
"""
import csv
import re
import os
from collections import defaultdict
from datetime import datetime

# Paths
CSHARP_LOG = r"C:\Users\HMz\Documents\Source\KitaTrader\c_sharp_log.txt"
PYTHON_LOG = r"C:\Users\HMz\Documents\Source\KitaTrader\python_log.txt"

# Debug log file
LOG_DIR = os.path.dirname(os.path.abspath(__file__))
DEBUG_LOG = os.path.join(LOG_DIR, "compare_sma_results_debug.log")

def debug_log(message):
    """Write debug message to log file"""
    with open(DEBUG_LOG, 'a', encoding='utf-8') as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        f.write(f"[{timestamp}] {message}\n")
        f.flush()

def parse_log_line(line):
    """Parse a single log line and extract FINAL_BAR parts"""
    if 'FINAL_BAR|' not in line:
        return None
    
    # Extract the FINAL_BAR part
    if '| Info | FINAL_BAR|' in line:
        final_bar_part = line.split('| Info | FINAL_BAR|')[1].strip()
    else:
        idx = line.find('FINAL_BAR|')
        if idx >= 0:
            final_bar_part = line[idx + len('FINAL_BAR|'):].strip()
        else:
            return None
            
    parts = final_bar_part.split('|')
    # Required: TF(0), Time(1), O(2), H(3), L(4), C(5), V(6), SMA_O(7), SMA_H(8), SMA_L(9), SMA_C(10)
    if len(parts) < 11:
        return None
        
    tf = parts[0]
    res = {
        'tf': tf,
        'time': parts[1],
        'open': parts[2],
        'high': parts[3],
        'low': parts[4],
        'close': parts[5],
        'volume': parts[6],
        'sma_open': parts[7] if len(parts) > 7 and parts[7] else None,
        'sma_high': parts[8] if len(parts) > 8 and parts[8] else None,
        'sma_low': parts[9] if len(parts) > 9 and parts[9] else None,
        'sma_close': parts[10] if len(parts) > 10 and parts[10] else None
    }
    return res

def parse_log(log_path, label):
    """Parse log file and extract FINAL_BAR entries"""
    bars = defaultdict(list)
    debug_log(f"Parsing {label} log file: {log_path}")
    
    if not os.path.exists(log_path):
        debug_log(f"File not found: {log_path}")
        return bars
        
    with open(log_path, 'r', encoding='utf-8') as f:
        line_count = 0
        final_bar_count = 0
        for line in f:
            line_count += 1
            data = parse_log_line(line)
            if data:
                final_bar_count += 1
                tf = data.pop('tf')
                bars[tf].append(data)
    
    debug_log(f"Parsed {line_count} lines from {label} log, found {final_bar_count} FINAL_BAR entries")
    for tf, tf_bars in bars.items():
        debug_log(f"  {tf}: {len(tf_bars)} bars")
        print(f"    {tf}: {len(tf_bars)} bars")
    return bars

def compare_results(csharp_bars, python_bars, timeframe):
    """Compare C# and Python results"""
    debug_log(f"Comparing {timeframe} bars")
    
    csharp_dict = {bar['time']: bar for bar in csharp_bars}
    python_dict = {bar['time']: bar for bar in python_bars}
    
    common_times = set(csharp_dict.keys()) & set(python_dict.keys())
    only_csharp = set(csharp_dict.keys()) - set(python_dict.keys())
    only_python = set(python_dict.keys()) - set(csharp_dict.keys())
    
    print(f"{timeframe}: Common={len(common_times)}, Only_C#={len(only_csharp)}, Only_Python={len(only_python)}")
    
    # Compare prices and volume
    ohlcv_mismatches = []
    sma_mismatches = []
    TOLERANCE_PRICE = 1e-12
    TOLERANCE_SMA = 1.1e-5
    
    def is_diff(v1, v2, tol):
        if v1 is None and v2 is None: return False
        if v1 is None or v2 is None: return True
        try:
            return abs(float(v1) - float(v2)) > tol
        except:
            return v1 != v2

    for time in sorted(common_times):
        cs = csharp_dict[time]
        py = python_dict[time]
        
        # OHLCV checks
        if any(is_diff(cs[f], py[f], TOLERANCE_PRICE) for f in ['open', 'high', 'low', 'close', 'volume']):
            ohlcv_mismatches.append({'time': time, 'cs': cs, 'py': py})
            
        # SMA checks (OHLC only)
        for field in ['sma_open', 'sma_high', 'sma_low', 'sma_close']:
            if field not in cs or field not in py: continue
            if is_diff(cs[field], py[field], TOLERANCE_SMA):
                sma_mismatches.append({'time': time, 'field': field, 'cs': cs[field], 'py': py[field]})
                
    print(f"  OHLCV mismatches: {len(ohlcv_mismatches)}")
    print(f"  SMA mismatches: {len(sma_mismatches)}")
    
    debug_log(f"OHLCV mismatches: {len(ohlcv_mismatches)}")
    if ohlcv_mismatches:
        for mm in ohlcv_mismatches[:5]:
            debug_log(f"  MM at {mm['time']}:")
            debug_log(f"    CS: O={mm['cs']['open']}, H={mm['cs']['high']}, L={mm['cs']['low']}, C={mm['cs']['close']}, V={mm['cs']['volume']}")
            debug_log(f"    PY: O={mm['py']['open']}, H={mm['py']['high']}, L={mm['py']['low']}, C={mm['py']['close']}, V={mm['py']['volume']}")
            
    debug_log(f"SMA mismatches: {len(sma_mismatches)}")
    if sma_mismatches:
        for mm in sma_mismatches[:10]:
            debug_log(f"  MM at {mm['time']}, field {mm['field']}: CS={mm['cs']} vs PY={mm['py']}")

def main():
    if os.path.exists(DEBUG_LOG): os.remove(DEBUG_LOG)
    print("SMA Comparison - Starting...")
    print("  Reading C# log file...")
    csharp_bars = parse_log(CSHARP_LOG, "C#")
    print("  Reading Python log file...")
    python_bars = parse_log(PYTHON_LOG, "Python")
    
    print("\nComparing results...")
    for tf in ['M1', 'M5', 'H1', 'H4']:
        if tf in csharp_bars and tf in python_bars:
            print(f"\nComparing {tf} bars...")
            compare_results(csharp_bars[tf], python_bars[tf], tf)
    
    print("-" * 80)
    print(f"Debug log: {DEBUG_LOG}")

if __name__ == "__main__":
    main()
