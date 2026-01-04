"""
Compare Python bar generation with C# bar generation
"""
import csv
import re
from datetime import datetime
from collections import defaultdict

def parse_csharp_log(log_file):
    """Parse C# log file and extract FINAL_BAR entries"""
    bars = defaultdict(list)
    
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            if 'FINAL_BAR' in line:
                # Format: ... | Info | FINAL_BAR|M1|2025-12-02 00:00:00|Open|High|Low|Close|Volume|...
                # Extract the part after "FINAL_BAR|"
                idx = line.find('FINAL_BAR|')
                if idx >= 0:
                    data_part = line[idx + len('FINAL_BAR|'):].strip()
                    parts = data_part.split('|')
                    if len(parts) >= 7:
                        timeframe = parts[0]
                        time_str = parts[1]
                        try:
                            time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                            open_val = float(parts[2])
                            high_val = float(parts[3])
                            low_val = float(parts[4])
                            close_val = float(parts[5])
                            volume = int(parts[6])
                            
                            bars[timeframe].append({
                                'time': time,
                                'open': open_val,
                                'high': high_val,
                                'low': low_val,
                                'close': close_val,
                                'volume': volume
                            })
                        except (ValueError, IndexError) as e:
                            print(f"Error parsing line: {line[:150]}... Error: {e}")
    
    # Sort by time
    for tf in bars:
        bars[tf].sort(key=lambda x: x['time'])
    
    return bars

def parse_python_csv(csv_file):
    """Parse Python CSV file"""
    bars = []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                time = datetime.strptime(row['Time'], "%Y-%m-%d %H:%M:%S")
                bars.append({
                    'time': time,
                    'open': float(row['Open']) if row['Open'] else None,
                    'high': float(row['High']) if row['High'] else None,
                    'low': float(row['Low']) if row['Low'] else None,
                    'close': float(row['Close']) if row['Close'] else None,
                    'volume': int(row['Volume']) if row['Volume'] else None
                })
            except (ValueError, KeyError) as e:
                print(f"Error parsing row: {row}... Error: {e}")
    
    return bars

def compare_bars(csharp_bars, python_bars, timeframe):
    """Compare C# and Python bars"""
    print(f"\n{'='*80}")
    print(f"Comparing {timeframe} bars")
    print(f"{'='*80}")
    
    csharp_count = len(csharp_bars)
    python_count = len(python_bars)
    
    print(f"C# bars: {csharp_count}")
    print(f"Python bars: {python_count}")
    print(f"Difference: {abs(csharp_count - python_count)}")
    
    # Match bars by time
    csharp_dict = {bar['time']: bar for bar in csharp_bars}
    python_dict = {bar['time']: bar for bar in python_bars}
    
    all_times = sorted(set(list(csharp_dict.keys()) + list(python_dict.keys())))
    
    matches = 0
    mismatches = 0
    missing_csharp = 0
    missing_python = 0
    
    mismatch_details = []
    
    for time in all_times:
        csharp_bar = csharp_dict.get(time)
        python_bar = python_dict.get(time)
        
        if csharp_bar and python_bar:
            # Compare values
            tolerance = 0.00001  # For floating point comparison
            
            open_match = abs(csharp_bar['open'] - python_bar['open']) < tolerance if python_bar['open'] is not None else False
            high_match = abs(csharp_bar['high'] - python_bar['high']) < tolerance if python_bar['high'] is not None else False
            low_match = abs(csharp_bar['low'] - python_bar['low']) < tolerance if python_bar['low'] is not None else False
            close_match = abs(csharp_bar['close'] - python_bar['close']) < tolerance if python_bar['close'] is not None else False
            volume_match = csharp_bar['volume'] == python_bar['volume'] if python_bar['volume'] is not None else False
            
            if open_match and high_match and low_match and close_match and volume_match:
                matches += 1
            else:
                mismatches += 1
                mismatch_details.append({
                    'time': time,
                    'csharp': csharp_bar,
                    'python': python_bar,
                    'open_match': open_match,
                    'high_match': high_match,
                    'low_match': low_match,
                    'close_match': close_match,
                    'volume_match': volume_match
                })
        elif csharp_bar:
            missing_python += 1
        elif python_bar:
            missing_csharp += 1
    
    print(f"\nMatches: {matches}")
    print(f"Mismatches: {mismatches}")
    print(f"Missing in Python: {missing_csharp}")
    print(f"Missing in C#: {missing_python}")
    
    # Show date ranges
    if csharp_bars:
        csharp_start = min(bar['time'] for bar in csharp_bars)
        csharp_end = max(bar['time'] for bar in csharp_bars)
        print(f"\nC# date range: {csharp_start} to {csharp_end}")
    
    if python_bars:
        python_start = min(bar['time'] for bar in python_bars)
        python_end = max(bar['time'] for bar in python_bars)
        print(f"Python date range: {python_start} to {python_end}")
    
    # Show first 10 matches to verify all OHLCV values
    if matches > 0:
        print(f"\nFirst 10 matching bars (full OHLCV verification):")
        match_count = 0
        for time in all_times:
            if time in csharp_dict and time in python_dict:
                csharp_bar = csharp_dict[time]
                python_bar = python_dict[time]
                if match_count < 10:
                    tolerance = 0.00001
                    o_match = abs(csharp_bar['open'] - python_bar['open']) < tolerance if python_bar['open'] is not None else False
                    h_match = abs(csharp_bar['high'] - python_bar['high']) < tolerance if python_bar['high'] is not None else False
                    l_match = abs(csharp_bar['low'] - python_bar['low']) < tolerance if python_bar['low'] is not None else False
                    c_match = abs(csharp_bar['close'] - python_bar['close']) < tolerance if python_bar['close'] is not None else False
                    v_match = csharp_bar['volume'] == python_bar['volume'] if python_bar['volume'] is not None else False
                    
                    py_open = f"{python_bar['open']:.5f}" if python_bar['open'] is not None else "N/A"
                    py_high = f"{python_bar['high']:.5f}" if python_bar['high'] is not None else "N/A"
                    py_low = f"{python_bar['low']:.5f}" if python_bar['low'] is not None else "N/A"
                    py_close = f"{python_bar['close']:.5f}" if python_bar['close'] is not None else "N/A"
                    py_vol = python_bar['volume'] if python_bar['volume'] is not None else "N/A"
                    
                    print(f"  {time}:")
                    print(f"    Open:   C#={csharp_bar['open']:.5f}, Py={py_open}, Match={o_match}")
                    print(f"    High:   C#={csharp_bar['high']:.5f}, Py={py_high}, Match={h_match}")
                    print(f"    Low:    C#={csharp_bar['low']:.5f}, Py={py_low}, Match={l_match}")
                    print(f"    Close:  C#={csharp_bar['close']:.5f}, Py={py_close}, Match={c_match}")
                    print(f"    Volume: C#={csharp_bar['volume']}, Py={py_vol}, Match={v_match}")
                    match_count += 1
    
    # Show first 10 mismatches
    if mismatch_details:
        print(f"\nFirst 10 mismatches:")
        for i, detail in enumerate(mismatch_details[:10]):
            print(f"\n  Mismatch {i+1} at {detail['time']}:")
            print(f"    C#:   O={detail['csharp']['open']:.5f}, H={detail['csharp']['high']:.5f}, L={detail['csharp']['low']:.5f}, C={detail['csharp']['close']:.5f}, V={detail['csharp']['volume']}")
            print(f"    Py:   O={detail['python']['open']:.5f if detail['python']['open'] else 'N/A'}, H={detail['python']['high']:.5f if detail['python']['high'] else 'N/A'}, L={detail['python']['low']:.5f if detail['python']['low'] else 'N/A'}, C={detail['python']['close']:.5f if detail['python']['close'] else 'N/A'}, V={detail['python']['volume'] if detail['python']['volume'] else 'N/A'}")
            print(f"    Match: O={detail['open_match']}, H={detail['high_match']}, L={detail['low_match']}, C={detail['close_match']}, V={detail['volume_match']}")
    
    return matches, mismatches, missing_csharp, missing_python

def main():
    log_dir = r"C:\Users\HMz\Documents\cAlgo\Logfiles"
    
    # Parse C# log - use the December 1st specific log file
    csharp_log = r"C:\Users\HMz\Documents\cAlgo\Data\cBots\OHLCTestBot\29639f65-52c0-4443-a8c7-b6511867444a\Backtesting\log.txt"
    print(f"Parsing C# log (Dec 1st only): {csharp_log}")
    csharp_bars_all = parse_csharp_log(csharp_log)
    
    # Parse Python CSV files and filter to December 1st only for fair comparison
    timeframes = ['M1', 'M5', 'H1', 'H4']
    dec1_date = datetime(2025, 12, 1)
    dec2_date = datetime(2025, 12, 2)
    
    for tf in timeframes:
        python_csv = f"{log_dir}\\OHLC_Test_Python_{tf}.csv"
        print(f"\nParsing Python CSV: {python_csv}")
        
        if tf in csharp_bars_all:
            csharp_bars = csharp_bars_all[tf]
            python_bars_all = parse_python_csv(python_csv)
            
            # Filter Python bars to December 1st only
            python_bars = [bar for bar in python_bars_all if dec1_date <= bar['time'] < dec2_date]
            
            print(f"Filtered Python bars to Dec 1st only: {len(python_bars)} bars (from {len(python_bars_all)} total)")
            
            compare_bars(csharp_bars, python_bars, tf)
        else:
            print(f"No C# bars found for {tf}")
            # Still show Python bars for reference
            python_bars_all = parse_python_csv(python_csv)
            python_bars = [bar for bar in python_bars_all if dec1_date <= bar['time'] < dec2_date]
            if python_bars:
                print(f"  Python has {len(python_bars)} bars for Dec 1st (no C# to compare)")

if __name__ == '__main__':
    main()
