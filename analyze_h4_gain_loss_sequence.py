"""
Analyze H4 gain/loss sequence to understand EMA initialization differences
Compare the first N gain/loss values between Python and C# to see if sequences match
"""
import re
import math
from datetime import datetime

def extract_h4_gain_loss_sequence(log_file, is_python=True):
    """Extract H4 gain/loss sequence in chronological order"""
    sequence = []
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
                    gain = None
                    loss = None
                    
                    for part in parts[3:]:
                        if '=' in part:
                            key, value = part.split('=', 1)
                            try:
                                if key == 'RSI_GAIN':
                                    gain = float(value) if value.lower() != 'nan' else float('nan')
                                elif key == 'RSI_LOSS':
                                    loss = float(value) if value.lower() != 'nan' else float('nan')
                            except (ValueError, TypeError):
                                pass
                    
                    if gain is not None and loss is not None:
                        sequence.append({
                            'time': current_bar['time'],
                            'open': current_bar['open'],
                            'close': current_bar['close'],
                            'gain': gain,
                            'loss': loss
                        })
                    current_bar = None
            elif not is_python and 'FINAL_BAR|H4|' in line:
                final_bar_start = line.find('FINAL_BAR|H4|')
                if final_bar_start >= 0:
                    final_bar_line = line[final_bar_start:].strip()
                    parts = final_bar_line.split('|')
                    if len(parts) >= 7:
                        time_str = parts[2]
                        open_price = float(parts[3])
                        close_price = float(parts[6])
                        
                        # C# RSI is likely initialized with ClosePrices, so calculate gain/loss from Close prices
                        # Calculate gain/loss from previous bar's close (if available)
                        if len(sequence) > 0:
                            prev_close = sequence[-1]['close']
                            if close_price > prev_close:
                                gain = close_price - prev_close
                                loss = 0.0
                            elif close_price < prev_close:
                                gain = 0.0
                                loss = prev_close - close_price
                            else:
                                gain = 0.0
                                loss = 0.0
                        else:
                            # First bar - no gain/loss (need previous bar)
                            gain = 0.0
                            loss = 0.0
                        
                        sequence.append({
                            'time': time_str,
                            'open': open_price,
                            'close': close_price,
                            'gain': gain,
                            'loss': loss
                        })
    
    return sequence

def calculate_ema_step_by_step(values, periods):
    """
    Calculate EMA step by step to see initialization
    EMA uses alpha = 2.0 / (periods + 1)
    First value is source[0] (not SMA)
    """
    if len(values) == 0:
        return []
    
    alpha = 2.0 / (periods + 1.0)
    ema_values = []
    
    # First value: use source[0] directly (like C# EMA does)
    ema = values[0]
    ema_values.append(ema)
    
    # Subsequent values: EMA formula
    for i in range(1, len(values)):
        ema = alpha * values[i] + (1.0 - alpha) * ema
        ema_values.append(ema)
    
    return ema_values

def main():
    python_log = r"C:\Users\HMz\Documents\cAlgo\Logfiles\OHLCTestBot_Python.log"
    csharp_log = r"C:\Users\HMz\Documents\cAlgo\Data\cBots\OHLCTestBot\29639f65-52c0-4443-a8c7-b6511867444a\Backtesting\log.txt"
    
    print("=== H4 GAIN/LOSS SEQUENCE ANALYSIS ===")
    print()
    
    python_sequence = extract_h4_gain_loss_sequence(python_log, is_python=True)
    csharp_sequence = extract_h4_gain_loss_sequence(csharp_log, is_python=False)
    
    print(f"Python sequence length: {len(python_sequence)}")
    print(f"C# sequence length: {len(csharp_sequence)}")
    print()
    
    # Compare first 30 entries
    min_len = min(len(python_sequence), len(csharp_sequence), 30)
    
    print(f"=== FIRST {min_len} GAIN/LOSS VALUES COMPARISON ===")
    print()
    
    gains_match = True
    losses_match = True
    
    for i in range(min_len):
        py = python_sequence[i]
        cs = csharp_sequence[i]
        
        gain_diff = abs(py['gain'] - cs['gain'])
        loss_diff = abs(py['loss'] - cs['loss'])
        
        match_str = ""
        if gain_diff > 0.00001 or loss_diff > 0.00001:
            match_str = " [MISMATCH]"
            gains_match = False
            losses_match = False
        
        print(f"{i+1}. {py['time']}:")
        print(f"   Gain: Py={py['gain']:.8f}, C#={cs['gain']:.8f}, Diff={gain_diff:.10f}")
        print(f"   Loss: Py={py['loss']:.8f}, C#={cs['loss']:.8f}, Diff={loss_diff:.10f}{match_str}")
    
    print()
    print(f"Gains match: {gains_match}")
    print(f"Losses match: {losses_match}")
    print()
    
    # Calculate EMA step by step for first 30 values
    rsi_period = 14
    ema_periods = 2 * rsi_period - 1  # 27
    
    print(f"=== EMA CALCULATION (periods={ema_periods}) ===")
    print()
    
    # Extract gain and loss sequences
    py_gains = [e['gain'] for e in python_sequence[:30]]
    py_losses = [e['loss'] for e in python_sequence[:30]]
    cs_gains = [e['gain'] for e in csharp_sequence[:30]]
    cs_losses = [e['loss'] for e in csharp_sequence[:30]]
    
    # Calculate EMAs step by step
    py_ema_gains = calculate_ema_step_by_step(py_gains, ema_periods)
    py_ema_losses = calculate_ema_step_by_step(py_losses, ema_periods)
    cs_ema_gains = calculate_ema_step_by_step(cs_gains, ema_periods)
    cs_ema_losses = calculate_ema_step_by_step(cs_losses, ema_periods)
    
    print("First 10 EMA Gain values:")
    for i in range(min(10, len(py_ema_gains), len(cs_ema_gains))):
        diff = abs(py_ema_gains[i] - cs_ema_gains[i])
        print(f"  {i}: Py={py_ema_gains[i]:.10f}, C#={cs_ema_gains[i]:.10f}, Diff={diff:.10f}")
    
    print()
    print("First 10 EMA Loss values:")
    for i in range(min(10, len(py_ema_losses), len(cs_ema_losses))):
        diff = abs(py_ema_losses[i] - cs_ema_losses[i])
        print(f"  {i}: Py={py_ema_losses[i]:.10f}, C#={cs_ema_losses[i]:.10f}, Diff={diff:.10f}")

if __name__ == "__main__":
    main()
