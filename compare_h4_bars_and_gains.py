"""
Compare H4 bars and gains/losses between Python and C#
Check if the source values (Close prices) are identical, and if gains/losses are calculated correctly
"""
import re
from datetime import datetime

def extract_h4_bars_and_indicators(log_file, is_python=True):
    """Extract H4 bars and RSI internal values"""
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
                    open_price = float(parts[3])
                    high_price = float(parts[4])
                    low_price = float(parts[5])
                    close_price = float(parts[6])
                    volume = int(parts[7])
                    
                    current_bar = {
                        'time': time_str,
                        'open': open_price,
                        'high': high_price,
                        'low': low_price,
                        'close': close_price,
                        'volume': volume
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
            elif not is_python and 'FINAL_BAR|H4|' in line:
                final_bar_start = line.find('FINAL_BAR|H4|')
                if final_bar_start >= 0:
                    final_bar_line = line[final_bar_start:].strip()
                    parts = final_bar_line.split('|')
                    if len(parts) >= 7:
                        time_str = parts[2]
                        open_price = float(parts[3])
                        high_price = float(parts[4])
                        low_price = float(parts[5])
                        close_price = float(parts[6])
                        volume = int(parts[7])
                        
                        data[time_str] = {
                            'bar': {
                                'time': time_str,
                                'open': open_price,
                                'high': high_price,
                                'low': low_price,
                                'close': close_price,
                                'volume': volume
                            }
                        }
    return data

def main():
    python_log = r"C:\Users\HMz\Documents\cAlgo\Logfiles\OHLCTestBot_Python.log"
    csharp_log = r"C:\Users\HMz\Documents\cAlgo\Data\cBots\OHLCTestBot\29639f65-52c0-4443-a8c7-b6511867444a\Backtesting\log.txt"
    
    print("=== H4 BARS AND GAINS/LOSSES COMPARISON ===")
    print()
    
    python_data = extract_h4_bars_and_indicators(python_log, is_python=True)
    csharp_data = extract_h4_bars_and_indicators(csharp_log, is_python=False)
    
    print(f"Python H4 entries: {len(python_data)}")
    print(f"C# H4 entries: {len(csharp_data)}")
    print()
    
    # Find common timestamps
    common_times = sorted(set(python_data.keys()) & set(csharp_data.keys()))
    print(f"Common H4 entries: {len(common_times)}")
    print()
    
    # Compare bars and calculate gains/losses
    print("=== FIRST 10 H4 ENTRIES COMPARISON ===")
    for i, time_str in enumerate(common_times[:10], 1):
        py = python_data[time_str]
        cs = csharp_data[time_str]
        
        py_bar = py['bar']
        cs_bar = cs['bar']
        
        print(f"\n{i}. {time_str}:")
        
        # Compare Close prices
        close_diff = abs(py_bar['close'] - cs_bar['close'])
        print(f"   Close: Py={py_bar['close']:.5f}, C#={cs_bar['close']:.5f}, Diff={close_diff:.10f}")
        
        # Calculate gain/loss from previous bar (if available)
        # NOTE: RSI is now initialized with ClosePrices to match C# behavior
        if i > 1:
            prev_time = common_times[i-2]
            prev_py = python_data[prev_time]
            prev_cs = csharp_data[prev_time]
            
            # Use Close prices since RSI is initialized with ClosePrices
            prev_py_close = prev_py['bar']['close']
            prev_cs_close = prev_cs['bar']['close']
            
            py_gain = max(0.0, py_bar['close'] - prev_py_close)
            py_loss = max(0.0, prev_py_close - py_bar['close'])
            cs_gain = max(0.0, cs_bar['close'] - prev_cs_close)
            cs_loss = max(0.0, prev_cs_close - cs_bar['close'])
            
            print(f"   Calculated Gain (from Close): Py={py_gain:.8f}, C#={cs_gain:.8f}, Diff={abs(py_gain - cs_gain):.10f}")
            print(f"   Calculated Loss (from Close): Py={py_loss:.8f}, C#={cs_loss:.8f}, Diff={abs(py_loss - cs_loss):.10f}")
            
            if 'gain' in py:
                print(f"   Logged Gain: Py={py['gain']:.8f}, Diff={abs(py['gain'] - py_gain):.10f}")
            if 'loss' in py:
                print(f"   Logged Loss: Py={py['loss']:.8f}, Diff={abs(py['loss'] - py_loss):.10f}")
        
        # Show RSI and EMA values
        if 'rsi' in py:
            print(f"   RSI: Py={py['rsi']:.5f}")
            if 'ema_gain' in py and py['ema_gain'] is not None:
                print(f"   EMA Gain: {py['ema_gain']:.10f}")
            if 'ema_loss' in py and py['ema_loss'] is not None:
                print(f"   EMA Loss: {py['ema_loss']:.10f}")

if __name__ == "__main__":
    main()
