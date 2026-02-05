"""
Analyze how Source[0] and Source[1] are initialized in Python vs C#
Check if there's a difference in the first source values
"""
import re
from datetime import datetime, timedelta

def analyze_source_values():
    python_log = r"C:\Users\HMz\Documents\cAlgo\Logfiles\OHLCTestBot_Python.log"
    csharp_log = r"C:\Users\HMz\Documents\cAlgo\Data\cBots\OHLCTestBot\29639f65-52c0-4443-a8c7-b6511867444a\Backtesting\log.txt"
    output_file = r"C:\Users\HMz\Documents\cAlgo\Logfiles\source_initialization_analysis.txt"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=== SOURCE INITIALIZATION ANALYSIS ===\n\n")
        
        # Extract first few H4 bars
        py_bars = []
        cs_bars = []
        
        with open(python_log, 'r', encoding='utf-8') as py_log:
            for line in py_log:
                if line.startswith('FINAL_BAR|H4|'):
                    parts = line.strip().split('|')
                    if len(parts) >= 7:
                        time_str = parts[2]
                        if time_str.startswith('2025-12-04'):
                            continue
                        close_price = float(parts[6])
                        py_bars.append({
                            'time': time_str,
                            'close': close_price
                        })
        
        with open(csharp_log, 'r', encoding='utf-8') as cs_log:
            for line in cs_log:
                if 'FINAL_BAR|H4|' in line:
                    final_bar_start = line.find('FINAL_BAR|H4|')
                    if final_bar_start >= 0:
                        final_bar_line = line[final_bar_start:].strip()
                        parts = final_bar_line.split('|')
                        if len(parts) >= 7:
                            time_str = parts[2]
                            close_price = float(parts[6])
                            cs_bars.append({
                                'time': time_str,
                                'close': close_price
                            })
        
        f.write(f"Python H4 bars: {len(py_bars)}\n")
        f.write(f"C# H4 bars: {len(cs_bars)}\n\n")
        
        # Show first 5 bars
        f.write("First 5 Python H4 bars:\n")
        for i, bar in enumerate(py_bars[:5], 0):
            f.write(f"  Index {i}: {bar['time']}, Close: {bar['close']:.5f}\n")
        
        f.write("\nFirst 5 C# H4 bars:\n")
        for i, bar in enumerate(cs_bars[:5], 0):
            f.write(f"  Index {i}: {bar['time']}, Close: {bar['close']:.5f}\n")
        
        # Calculate what Source[0] would be for Python based on first bar's gain
        if len(py_bars) > 0:
            first_bar_close = py_bars[0]['close']
            # Python logged Gain = 0.00079 for first bar
            # If Gain = source[1] - source[0] = 0.00079
            # Then source[0] = source[1] - 0.00079 = first_bar_close - 0.00079
            source_0_calculated = first_bar_close - 0.00079
            f.write(f"\nPython first bar Close: {first_bar_close:.5f}\n")
            f.write(f"Python logged Gain for first bar: 0.00079\n")
            f.write(f"Calculated Source[0] (previous bar Close): {source_0_calculated:.5f}\n")
            f.write(f"This suggests Python Source[0] = {source_0_calculated:.5f}\n")
            
            # Check if this matches any logged bar
            f.write(f"\nChecking if Source[0] matches any logged bar:\n")
            for i, bar in enumerate(py_bars[:3]):
                diff = abs(bar['close'] - source_0_calculated)
                f.write(f"  Bar {i} ({bar['time']}): Close={bar['close']:.5f}, Diff={diff:.8f}\n")
            
            # Check if Source[0] would be the previous H4 bar (4 hours before)
            first_bar_time = datetime.strptime(py_bars[0]['time'], '%Y-%m-%d %H:%M:%S')
            prev_h4_time = first_bar_time - timedelta(hours=4)
            f.write(f"\nPrevious H4 bar time (4 hours before first): {prev_h4_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"This bar would be in warmup period: {prev_h4_time >= datetime(2025, 11, 24, 0, 0, 0) and prev_h4_time < datetime(2025, 12, 1, 0, 0, 0)}\n")
        
        # For C#, check what Source[0] would be
        if len(cs_bars) > 0:
            first_bar_close = cs_bars[0]['close']
            # C# has Gain = 0.0 for first bar
            # This suggests Source[0] = Source[1] (or Source[0] doesn't exist)
            f.write(f"\nC# first bar Close: {first_bar_close:.5f}\n")
            f.write(f"C# logged Gain for first bar: 0.0\n")
            f.write(f"This suggests C# Source[0] = Source[1] = {first_bar_close:.5f} (or Source[0] doesn't exist)\n")

if __name__ == "__main__":
    analyze_source_values()
