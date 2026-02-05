"""
Compare RSI internal EMA values (gains/losses) between C# and Python
This script extracts and compares the internal EMA values to debug RSI differences
"""
import re
import math
from datetime import datetime

def extract_rsi_internal_values(log_file, is_python=True):
    """Extract RSI and internal EMA values from log file"""
    rsi_data = {}
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            if is_python and line.startswith('FINAL_IND|'):
                parts = line.strip().split('|')
                if len(parts) >= 4:
                    tf = parts[1]
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
                        key = (tf, time_str)
                        rsi_data[key] = {
                            'rsi': rsi_val,
                            'ema_gain': ema_gain,
                            'ema_loss': ema_loss,
                            'gain': gain,
                            'loss': loss
                        }
            elif not is_python and 'FINAL_IND|' in line:
                # C# logs don't have internal EMA values yet, so we can only extract RSI
                final_ind_start = line.find('FINAL_IND|')
                if final_ind_start >= 0:
                    final_ind_line = line[final_ind_start:].strip()
                    parts = final_ind_line.split('|')
                    if len(parts) >= 4:
                        tf = parts[1]
                        time_str = parts[2]
                        for part in parts[3:]:
                            if part.startswith('RSI='):
                                try:
                                    rsi_val = float(part.split('=')[1])
                                    key = (tf, time_str)
                                    rsi_data[key] = {
                                        'rsi': rsi_val,
                                        'ema_gain': None,
                                        'ema_loss': None,
                                        'gain': None,
                                        'loss': None
                                    }
                                except (ValueError, TypeError):
                                    pass
    return rsi_data

def main():
    python_log = r"C:\Users\HMz\Documents\cAlgo\Logfiles\OHLCTestBot_Python.log"
    csharp_log = r"C:\Users\HMz\Documents\cAlgo\Data\cBots\OHLCTestBot\29639f65-52c0-4443-a8c7-b6511867444a\Backtesting\log.txt"
    
    print("=== RSI INTERNAL EMA COMPARISON ===")
    print("Extracting RSI and internal EMA values...")
    print()
    
    python_data = extract_rsi_internal_values(python_log, is_python=True)
    csharp_data = extract_rsi_internal_values(csharp_log, is_python=False)
    
    print(f"Python entries: {len(python_data)}")
    print(f"C# entries: {len(csharp_data)}")
    print()
    
    # Find common keys
    common_keys = set(python_data.keys()) & set(csharp_data.keys())
    print(f"Common entries: {len(common_keys)}")
    print()
    
    # Compare RSI values and show internal EMA values
    rsi_mismatches = []
    rsi_matches = []
    
    for key in sorted(common_keys):
        py_data = python_data[key]
        cs_data = csharp_data[key]
        
        py_rsi = py_data['rsi']
        cs_rsi = cs_data['rsi']
        rsi_diff = abs(py_rsi - cs_rsi)
        
        if rsi_diff > 0.00001:
            rsi_mismatches.append({
                'key': key,
                'python': py_data,
                'csharp': cs_data,
                'rsi_diff': rsi_diff
            })
        else:
            rsi_matches.append(key)
    
    print(f"RSI Matches: {len(rsi_matches)}")
    print(f"RSI Mismatches: {len(rsi_mismatches)}")
    print()
    
    if rsi_mismatches:
        print("=== RSI MISMATCHES WITH INTERNAL EMA VALUES (showing first 30) ===")
        for i, mm in enumerate(rsi_mismatches[:30], 1):
            tf, time_str = mm['key']
            py = mm['python']
            cs = mm['csharp']
            
            print(f"\n{i}. {tf} @ {time_str}:")
            print(f"   RSI: Py={py['rsi']:.5f}, C#={cs['rsi']:.5f}, Diff={mm['rsi_diff']:.8f}")
            
            if py['ema_gain'] is not None:
                print(f"   EMA Gain: Py={py['ema_gain']:.8f}")
            if py['ema_loss'] is not None:
                print(f"   EMA Loss: Py={py['ema_loss']:.8f}")
            if py['gain'] is not None:
                print(f"   Gain: Py={py['gain']:.8f}")
            if py['loss'] is not None:
                print(f"   Loss: Py={py['loss']:.8f}")
        
        # Group by timeframe
        print("\n=== MISMATCHES BY TIMEFRAME ===")
        for tf in ['M1', 'M5', 'H1', 'H4']:
            tf_mismatches = [mm for mm in rsi_mismatches if mm['key'][0] == tf]
            if tf_mismatches:
                avg_diff = sum(mm['rsi_diff'] for mm in tf_mismatches) / len(tf_mismatches)
                max_diff = max(mm['rsi_diff'] for mm in tf_mismatches)
                print(f"{tf}: {len(tf_mismatches)} mismatches, Avg diff: {avg_diff:.8f}, Max diff: {max_diff:.8f}")
                
                # Show internal EMA values for H4 mismatches (most problematic)
                if tf == 'H4' and len(tf_mismatches) > 0:
                    print(f"   H4 Internal EMA values (first 5 mismatches):")
                    for mm in tf_mismatches[:5]:
                        py = mm['python']
                        ema_gain_str = f"{py['ema_gain']:.8f}" if py['ema_gain'] is not None and not math.isnan(py['ema_gain']) else "N/A"
                        ema_loss_str = f"{py['ema_loss']:.8f}" if py['ema_loss'] is not None and not math.isnan(py['ema_loss']) else "N/A"
                        gain_str = f"{py['gain']:.8f}" if py['gain'] is not None and not math.isnan(py['gain']) else "N/A"
                        loss_str = f"{py['loss']:.8f}" if py['loss'] is not None and not math.isnan(py['loss']) else "N/A"
                        print(f"     {mm['key'][1]}: EMA_Gain={ema_gain_str}, "
                              f"EMA_Loss={ema_loss_str}, "
                              f"Gain={gain_str}, "
                              f"Loss={loss_str}")

if __name__ == "__main__":
    main()
