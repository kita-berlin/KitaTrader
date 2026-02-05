"""
Analyze the first bar and warmup period to understand why Python uses a previous bar
"""
import re
from datetime import datetime, timedelta

def analyze_warmup_bars():
    python_log = r"C:\Users\HMz\Documents\cAlgo\Logfiles\OHLCTestBot_Python.log"
    output_file = r"C:\Users\HMz\Documents\cAlgo\Logfiles\warmup_analysis.txt"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=== WARMUP PERIOD ANALYSIS ===\n\n")
        
        # Warmup period: 24.11.2025 to 01.12.2025
        warmup_start = datetime(2025, 11, 24, 0, 0, 0)
        backtest_start = datetime(2025, 12, 1, 0, 0, 0)
        first_logged_bar = datetime(2025, 11, 30, 22, 0, 0)
        
        f.write(f"Warmup Start: {warmup_start.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Backtest Start: {backtest_start.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"First logged H4 bar: {first_logged_bar.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Calculate expected previous H4 bar (4 hours before)
        prev_h4_bar = first_logged_bar - timedelta(hours=4)
        f.write(f"Previous H4 bar (4 hours before): {prev_h4_bar.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"This bar should be in warmup period: {prev_h4_bar >= warmup_start and prev_h4_bar < backtest_start}\n\n")
        
        # Extract all H4 bars from Python log
        h4_bars = []
        with open(python_log, 'r', encoding='utf-8') as py_log:
            for line in py_log:
                if line.startswith('FINAL_BAR|H4|'):
                    parts = line.strip().split('|')
                    if len(parts) >= 7:
                        time_str = parts[2]
                        try:
                            bar_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                            close_price = float(parts[6])
                            h4_bars.append({
                                'time': bar_time,
                                'time_str': time_str,
                                'close': close_price
                            })
                        except:
                            pass
        
        f.write(f"Total H4 bars in Python log: {len(h4_bars)}\n")
        f.write(f"First H4 bar: {h4_bars[0]['time_str'] if h4_bars else 'N/A'}\n")
        f.write(f"Last H4 bar: {h4_bars[-1]['time_str'] if h4_bars else 'N/A'}\n\n")
        
        # Check if there's a bar before the first logged bar
        if h4_bars:
            first_bar = h4_bars[0]
            f.write(f"First logged bar: {first_bar['time_str']}, Close: {first_bar['close']:.5f}\n")
            
            # Calculate expected previous bar
            expected_prev_time = first_bar['time'] - timedelta(hours=4)
            f.write(f"Expected previous bar time: {expected_prev_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Expected previous bar would be in warmup: {expected_prev_time >= warmup_start and expected_prev_time < backtest_start}\n\n")
            
            # Check Python's logged gain for first bar
            with open(python_log, 'r', encoding='utf-8') as py_log:
                for line in py_log:
                    if line.startswith('FINAL_IND|H4|') and first_bar['time_str'] in line:
                        parts = line.strip().split('|')
                        for part in parts[3:]:
                            if '=' in part:
                                key, value = part.split('=', 1)
                                if key == 'RSI_GAIN':
                                    f.write(f"Python logged Gain for first bar: {value}\n")
                                elif key == 'RSI_LOSS':
                                    f.write(f"Python logged Loss for first bar: {value}\n")
                        break
            
            # Calculate what the previous close would be based on the gain
            if h4_bars:
                first_close = first_bar['close']
                # If gain = 0.00079, then prev_close = first_close - 0.00079
                prev_close_calculated = first_close - 0.00079
                f.write(f"\nIf Gain = 0.00079, previous Close would be: {prev_close_calculated:.5f}\n")
                f.write(f"This suggests Python uses a previous bar with Close = {prev_close_calculated:.5f}\n")

if __name__ == "__main__":
    analyze_warmup_bars()
