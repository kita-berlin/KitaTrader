"""
Compare H4 RSI EMA values (EMA Gain and EMA Loss) between Python and C#
Since C# doesn't log EMA values directly, we'll compare Python's logged EMA values
with what they should be based on the gain/loss sequences
"""
import re
import math
from datetime import datetime

def extract_h4_rsi_emas(log_file, is_python=True):
    """Extract H4 RSI and EMA values from log file"""
    data = {}
    current_bar = None
    
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            if is_python and line.startswith('FINAL_BAR|H4|'):
                parts = line.strip().split('|')
                if len(parts) >= 7:
                    time_str = parts[2]
                    if time_str.startswith('2025-12-04'):
                        continue
                    current_bar = {
                        'time': time_str,
                        'open': float(parts[3]),
                        'high': float(parts[4]),
                        'low': float(parts[5]),
                        'close': float(parts[6]),
                        'volume': int(parts[7])
                    }
            elif is_python and line.startswith('FINAL_IND|H4|') and current_bar:
                parts = line.strip().split('|')
                if len(parts) >= 4 and parts[2] == current_bar['time']:
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
                        data[current_bar['time']] = {
                            'bar': current_bar,
                            'rsi': rsi_val,
                            'ema_gain': ema_gain,
                            'ema_loss': ema_loss,
                            'gain': gain,
                            'loss': loss
                        }
                    current_bar = None
            elif not is_python and 'FINAL_IND|H4|' in line:
                final_ind_start = line.find('FINAL_IND|H4|')
                if final_ind_start >= 0:
                    final_ind_line = line[final_ind_start:].strip()
                    parts = final_ind_line.split('|')
                    if len(parts) >= 4:
                        time_str = parts[2]
                        rsi_val = None
                        for part in parts[3:]:
                            if part.startswith('RSI='):
                                try:
                                    rsi_val = float(part.split('=')[1])
                                    break
                                except (ValueError, TypeError):
                                    pass
                        
                        if rsi_val is not None:
                            data[time_str] = {
                                'rsi': rsi_val,
                                'ema_gain': None,  # C# doesn't log this
                                'ema_loss': None,  # C# doesn't log this
                                'gain': None,
                                'loss': None
                            }
    return data

def calculate_ema_from_sequence(gains_losses, period, start_index=0):
    """
    Calculate EMA from a sequence of gain/loss values
    EMA uses Wilder's smoothing: ema_periods = 2 * period - 1
    """
    if len(gains_losses) < period:
        return None
    
    # EMA period for Wilder's smoothing
    ema_periods = 2 * period - 1
    alpha = 2.0 / (ema_periods + 1.0)
    
    # Initialize with SMA of first 'period' values
    if start_index + period > len(gains_losses):
        return None
    
    sma = sum(gains_losses[start_index:start_index + period]) / period
    ema = sma
    
    # Calculate EMA for remaining values
    for i in range(start_index + period, len(gains_losses)):
        ema = alpha * gains_losses[i] + (1.0 - alpha) * ema
    
    return ema

def main():
    python_log = r"C:\Users\HMz\Documents\cAlgo\Logfiles\OHLCTestBot_Python.log"
    csharp_log = r"C:\Users\HMz\Documents\cAlgo\Data\cBots\OHLCTestBot\29639f65-52c0-4443-a8c7-b6511867444a\Backtesting\log.txt"
    
    print("=== H4 RSI EMA VALUES COMPARISON ===")
    print()
    
    python_data = extract_h4_rsi_emas(python_log, is_python=True)
    csharp_data = extract_h4_rsi_emas(csharp_log, is_python=False)
    
    print(f"Python H4 entries: {len(python_data)}")
    print(f"C# H4 entries: {len(csharp_data)}")
    print()
    
    # Find common timestamps
    common_times = sorted(set(python_data.keys()) & set(csharp_data.keys()))
    print(f"Common H4 entries: {len(common_times)}")
    print()
    
    # Build sequences of gains and losses from Python data
    # RSI period = 14, EMA periods = 2 * 14 - 1 = 27
    rsi_period = 14
    ema_periods = 2 * rsi_period - 1  # 27
    
    print(f"RSI Period: {rsi_period}")
    print(f"EMA Periods (Wilder's smoothing): {ema_periods}")
    print()
    
    # Extract gain/loss sequences
    gains_sequence = []
    losses_sequence = []
    times_sequence = []
    
    for time_str in sorted(python_data.keys()):
        if time_str.startswith('2025-12-04'):
            continue
        py = python_data[time_str]
        if py['gain'] is not None and py['loss'] is not None:
            gains_sequence.append(py['gain'])
            losses_sequence.append(py['loss'])
            times_sequence.append(time_str)
    
    print(f"Total gain/loss entries: {len(gains_sequence)}")
    print()
    
    # Compare EMA values for common timestamps
    print("=== H4 EMA VALUES COMPARISON (first 20 common entries) ===")
    rsi_mismatches = []
    
    for i, time_str in enumerate(common_times[:20], 1):
        if time_str.startswith('2025-12-04'):
            continue
        
        py = python_data[time_str]
        cs = csharp_data[time_str]
        
        # Find index in sequence
        try:
            seq_index = times_sequence.index(time_str)
        except ValueError:
            continue
        
        print(f"\n{i}. {time_str}:")
        print(f"   RSI: Py={py['rsi']:.5f}, C#={cs['rsi']:.5f}, Diff={abs(py['rsi'] - cs['rsi']):.8f}")
        
        if py['ema_gain'] is not None and not math.isnan(py['ema_gain']):
            print(f"   EMA Gain (logged): {py['ema_gain']:.10f}")
        if py['ema_loss'] is not None and not math.isnan(py['ema_loss']):
            print(f"   EMA Loss (logged): {py['ema_loss']:.10f}")
        
        if py['gain'] is not None:
            print(f"   Gain: {py['gain']:.8f}")
        if py['loss'] is not None:
            print(f"   Loss: {py['loss']:.8f}")
        
        # Calculate EMA from sequence up to this point
        if seq_index >= ema_periods - 1:
            calculated_ema_gain = calculate_ema_from_sequence(gains_sequence, rsi_period, max(0, seq_index - ema_periods + 1))
            calculated_ema_loss = calculate_ema_from_sequence(losses_sequence, rsi_period, max(0, seq_index - ema_periods + 1))
            
            if calculated_ema_gain is not None and py['ema_gain'] is not None:
                ema_gain_diff = abs(calculated_ema_gain - py['ema_gain'])
                print(f"   EMA Gain (calculated from sequence): {calculated_ema_gain:.10f}, Diff={ema_gain_diff:.10f}")
            if calculated_ema_loss is not None and py['ema_loss'] is not None:
                ema_loss_diff = abs(calculated_ema_loss - py['ema_loss'])
                print(f"   EMA Loss (calculated from sequence): {calculated_ema_loss:.10f}, Diff={ema_loss_diff:.10f}")
        
        if abs(py['rsi'] - cs['rsi']) > 0.01:
            rsi_mismatches.append({
                'time': time_str,
                'python': py,
                'csharp': cs,
                'rsi_diff': abs(py['rsi'] - cs['rsi'])
            })
    
    if rsi_mismatches:
        print(f"\n=== H4 RSI MISMATCHES SUMMARY ===")
        print(f"Total mismatches: {len(rsi_mismatches)}")
        avg_diff = sum(mm['rsi_diff'] for mm in rsi_mismatches) / len(rsi_mismatches)
        max_diff = max(mm['rsi_diff'] for mm in rsi_mismatches)
        print(f"Average RSI diff: {avg_diff:.8f}")
        print(f"Max RSI diff: {max_diff:.8f}")

if __name__ == "__main__":
    main()
