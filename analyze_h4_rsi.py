"""
Analyze H4 RSI mismatches in detail
Compare Python and C# RSI values for H4 timeframe
"""
import re
from datetime import datetime

def extract_h4_rsi_values(log_file, is_python=True):
    """Extract H4 RSI values with internal EMAs"""
    rsi_data = {}
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            if is_python and line.startswith('FINAL_IND|H4|'):
                parts = line.strip().split('|')
                if len(parts) >= 4:
                    time_str = parts[2]
                    if time_str.startswith('2025-12-04'):
                        continue
                    
                    rsi_val = None
                    ema_gain = None
                    ema_loss = None
                    gain = None
                    loss = None
                    
                    for part in parts[3:]:
                        if '=' in part:
                            key, value = part.split('=', 1)
                            try:
                                if key == 'RSI':
                                    rsi_val = float(value)
                                elif key == 'RSI_EMA_GAIN':
                                    ema_gain = float(value) if value.lower() != 'nan' else float('nan')
                                elif key == 'RSI_EMA_LOSS':
                                    ema_loss = float(value) if value.lower() != 'nan' else float('nan')
                                elif key == 'RSI_GAIN':
                                    gain = float(value) if value.lower() != 'nan' else float('nan')
                                elif key == 'RSI_LOSS':
                                    loss = float(value) if value.lower() != 'nan' else float('nan')
                            except (ValueError, TypeError):
                                pass
                    
                    if rsi_val is not None:
                        rsi_data[time_str] = {
                            'rsi': rsi_val,
                            'ema_gain': ema_gain,
                            'ema_loss': ema_loss,
                            'gain': gain,
                            'loss': loss
                        }
            elif not is_python and 'FINAL_IND|H4|' in line:
                final_ind_start = line.find('FINAL_IND|H4|')
                if final_ind_start >= 0:
                    final_ind_line = line[final_ind_start:].strip()
                    parts = final_ind_line.split('|')
                    if len(parts) >= 4:
                        time_str = parts[2]
                        for part in parts[3:]:
                            if part.startswith('RSI='):
                                try:
                                    rsi_val = float(part.split('=')[1])
                                    rsi_data[time_str] = {'rsi': rsi_val}
                                except (ValueError, TypeError):
                                    pass
    return rsi_data

def main():
    python_log = r"C:\Users\HMz\Documents\cAlgo\Logfiles\OHLCTestBot_Python.log"
    csharp_log = r"C:\Users\HMz\Documents\cAlgo\Data\cBots\OHLCTestBot\29639f65-52c0-4443-a8c7-b6511867444a\Backtesting\log.txt"
    
    print("=== H4 RSI DETAILED ANALYSIS ===")
    print()
    
    python_data = extract_h4_rsi_values(python_log, is_python=True)
    csharp_data = extract_h4_rsi_values(csharp_log, is_python=False)
    
    print(f"Python H4 entries: {len(python_data)}")
    print(f"C# H4 entries: {len(csharp_data)}")
    print()
    
    # Find common timestamps
    common_times = sorted(set(python_data.keys()) & set(csharp_data.keys()))
    print(f"Common H4 entries: {len(common_times)}")
    print()
    
    # Compare and show mismatches
    mismatches = []
    for time_str in common_times:
        py = python_data[time_str]
        cs = csharp_data[time_str]
        diff = abs(py['rsi'] - cs['rsi'])
        
        if diff > 0.00001:
            mismatches.append({
                'time': time_str,
                'python': py,
                'csharp': cs,
                'diff': diff
            })
    
    print(f"H4 RSI Mismatches: {len(mismatches)}")
    print()
    
    if mismatches:
        print("=== H4 RSI MISMATCHES (all) ===")
        for i, mm in enumerate(mismatches, 1):
            py = mm['python']
            cs = mm['csharp']
            print(f"\n{i}. {mm['time']}:")
            print(f"   RSI: Py={py['rsi']:.5f}, C#={cs['rsi']:.5f}, Diff={mm['diff']:.5f}")
            if py['ema_gain'] is not None:
                print(f"   EMA Gain: {py['ema_gain']:.8f}")
            if py['ema_loss'] is not None:
                print(f"   EMA Loss: {py['ema_loss']:.8f}")
            if py['gain'] is not None:
                print(f"   Gain: {py['gain']:.8f}")
            if py['loss'] is not None:
                print(f"   Loss: {py['loss']:.8f}")
            
            # Calculate what RSI should be from EMA values
            if py['ema_gain'] is not None and py['ema_loss'] is not None:
                if py['ema_loss'] != 0.0:
                    num3 = py['ema_gain'] / py['ema_loss']
                    calculated_rsi = 100.0 - 100.0 / (1.0 + num3)
                    print(f"   Calculated RSI from EMAs: {calculated_rsi:.5f} (should match Py={py['rsi']:.5f})")

if __name__ == "__main__":
    main()
