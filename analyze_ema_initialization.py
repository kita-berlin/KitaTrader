"""
Analyze EMA initialization for RSI internal EMAs
Check if the warmup period is sufficient and if EMAs are initialized correctly
"""
import re
from datetime import datetime

def extract_h4_rsi_sequence(log_file):
    """Extract H4 RSI values with internal EMAs in sequence"""
    rsi_data = []
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('FINAL_IND|H4|'):
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
                        rsi_data.append({
                            'time': time_str,
                            'rsi': rsi_val,
                            'ema_gain': ema_gain,
                            'ema_loss': ema_loss,
                            'gain': gain,
                            'loss': loss
                        })
    return rsi_data

def main():
    python_log = r"C:\Users\HMz\Documents\cAlgo\Logfiles\OHLCTestBot_Python.log"
    
    print("=== H4 RSI EMA INITIALIZATION ANALYSIS ===")
    print()
    
    rsi_data = extract_h4_rsi_sequence(python_log)
    
    print(f"Total H4 entries: {len(rsi_data)}")
    print()
    
    # RSI period = 14, EMA periods = 2 * 14 - 1 = 27
    # For H4 bars, we need at least 27 bars for EMA to be fully initialized
    print("RSI Configuration:")
    print("  RSI Period: 14")
    print("  EMA Periods (for gains/losses): 2 * 14 - 1 = 27")
    print("  H4 bars needed for full EMA initialization: 27")
    print()
    
    # Show first 30 entries to see initialization pattern
    print("=== FIRST 30 H4 ENTRIES (to check initialization) ===")
    for i, entry in enumerate(rsi_data[:30], 1):
        print(f"\n{i}. {entry['time']}:")
        print(f"   RSI: {entry['rsi']:.5f}")
        if entry['ema_gain'] is not None:
            print(f"   EMA Gain: {entry['ema_gain']:.10f}")
        if entry['ema_loss'] is not None:
            print(f"   EMA Loss: {entry['ema_loss']:.10f}")
        if entry['gain'] is not None:
            print(f"   Gain: {entry['gain']:.8f}")
        if entry['loss'] is not None:
            print(f"   Loss: {entry['loss']:.8f}")
        
        # Check if EMA values are stable (not changing dramatically)
        if i > 1:
            prev = rsi_data[i-2]
            if prev['ema_gain'] is not None and entry['ema_gain'] is not None:
                ema_gain_change = abs(entry['ema_gain'] - prev['ema_gain'])
                ema_loss_change = abs(entry['ema_loss'] - prev['ema_loss'])
                print(f"   EMA Gain Change: {ema_gain_change:.10f}")
                print(f"   EMA Loss Change: {ema_loss_change:.10f}")
    
    # Check if first entry is before or after warmup period
    print("\n=== WARMUP ANALYSIS ===")
    print("Warmup period: 7 days (168 hours)")
    print("H4 bars in 7 days: 168 / 4 = 42 bars")
    print("Required for EMA: 27 bars")
    print("Warmup should be sufficient: YES (42 > 27)")
    print()
    
    # Check if EMA values stabilize after 27 bars
    if len(rsi_data) >= 27:
        print("=== EMA STABILIZATION CHECK (after 27 bars) ===")
        first_ema_gain = rsi_data[0]['ema_gain']
        ema_gain_27 = rsi_data[26]['ema_gain'] if len(rsi_data) > 26 else None
        ema_gain_last = rsi_data[-1]['ema_gain']
        
        if first_ema_gain is not None and ema_gain_27 is not None:
            print(f"First EMA Gain: {first_ema_gain:.10f}")
            print(f"EMA Gain at bar 27: {ema_gain_27:.10f}")
            print(f"Last EMA Gain: {ema_gain_last:.10f}")
            print(f"Change from first to bar 27: {abs(ema_gain_27 - first_ema_gain):.10f}")
            print(f"Change from bar 27 to last: {abs(ema_gain_last - ema_gain_27):.10f}")

if __name__ == "__main__":
    main()
