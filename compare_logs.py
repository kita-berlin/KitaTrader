"""
Compare C# and Python log files for OHLCTestBot
Extracts FINAL_BAR entries and compares them
"""
import re
from datetime import datetime
from collections import defaultdict


def parse_log_file(log_file):
    """Parse log file and extract FINAL_BAR entries"""
    bars = defaultdict(list)
    
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            if 'FINAL_BAR' in line:
                # Format: timestamp | Info | FINAL_BAR|TF|Time|Open|High|Low|Close|Volume|SMA_O|SMA_H|SMA_L|SMA_C
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


def compare_logs(csharp_log, python_log):
    """Compare C# and Python log files"""
    print("="*80)
    print("Comparing C# and Python OHLCTestBot log files")
    print("="*80)
    
    print(f"\nParsing C# log: {csharp_log}")
    csharp_bars = parse_log_file(csharp_log)
    
    print(f"Parsing Python log: {python_log}")
    python_bars = parse_log_file(python_log)
    
    timeframes = ['M1', 'M5', 'H1', 'H4']
    
    for tf in timeframes:
        print(f"\n{'='*80}")
        print(f"Comparing {tf} bars")
        print(f"{'='*80}")
        
        csharp_tf = csharp_bars.get(tf, [])
        python_tf = python_bars.get(tf, [])
        
        print(f"C# {tf} bars: {len(csharp_tf)}")
        print(f"Python {tf} bars: {len(python_tf)}")
        print(f"Difference: {abs(len(csharp_tf) - len(python_tf))}")
        
        if not csharp_tf and not python_tf:
            print(f"No bars found for {tf} in either log")
            continue
        
        # Match bars by time
        csharp_dict = {bar['time']: bar for bar in csharp_tf}
        python_dict = {bar['time']: bar for bar in python_tf}
        
        all_times = sorted(set(list(csharp_dict.keys()) + list(python_dict.keys())))
        
        matches = 0
        mismatches = 0
        missing_csharp = 0
        missing_python = 0
        
        tolerance = 0.00001
        
        for time in all_times:
            csharp_bar = csharp_dict.get(time)
            python_bar = python_dict.get(time)
            
            if csharp_bar and python_bar:
                # Compare all OHLCV values
                open_match = abs(csharp_bar['open'] - python_bar['open']) < tolerance
                high_match = abs(csharp_bar['high'] - python_bar['high']) < tolerance
                low_match = abs(csharp_bar['low'] - python_bar['low']) < tolerance
                close_match = abs(csharp_bar['close'] - python_bar['close']) < tolerance
                volume_match = csharp_bar['volume'] == python_bar['volume']
                
                if open_match and high_match and low_match and close_match and volume_match:
                    matches += 1
                else:
                    mismatches += 1
                    if mismatches <= 10:
                        print(f"\n  Mismatch at {time}:")
                        print(f"    C#:   O={csharp_bar['open']:.5f}, H={csharp_bar['high']:.5f}, L={csharp_bar['low']:.5f}, C={csharp_bar['close']:.5f}, V={csharp_bar['volume']}")
                        print(f"    Py:   O={python_bar['open']:.5f}, H={python_bar['high']:.5f}, L={python_bar['low']:.5f}, C={python_bar['close']:.5f}, V={python_bar['volume']}")
                        print(f"    Match: O={open_match}, H={high_match}, L={low_match}, C={close_match}, V={volume_match}")
            elif csharp_bar:
                missing_python += 1
            elif python_bar:
                missing_csharp += 1
        
        print(f"\nMatches: {matches}")
        print(f"Mismatches: {mismatches}")
        print(f"Missing in Python: {missing_csharp}")
        print(f"Missing in C#: {missing_python}")
        
        # Show first 5 matches for verification
        if matches > 0:
            print(f"\nFirst 5 matching bars (verification):")
            match_count = 0
            for time in all_times:
                if time in csharp_dict and time in python_dict:
                    csharp_bar = csharp_dict[time]
                    python_bar = python_dict[time]
                    if match_count < 5:
                        print(f"  {time}: O={csharp_bar['open']:.5f}, H={csharp_bar['high']:.5f}, L={csharp_bar['low']:.5f}, C={csharp_bar['close']:.5f}, V={csharp_bar['volume']}")
                        match_count += 1


def main():
    csharp_log = r"C:\Users\HMz\Documents\cAlgo\Data\cBots\OHLCTestBot\29639f65-52c0-4443-a8c7-b6511867444a\Backtesting\log.txt"
    python_log = r"C:\Users\HMz\Documents\cAlgo\Logfiles\OHLCTestBot_Python.log"
    
    compare_logs(csharp_log, python_log)


if __name__ == '__main__':
    main()
