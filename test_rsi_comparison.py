"""
Test RSI comparison - write results to log file only
"""
import re

def main():
    python_log = r"C:\Users\HMz\Documents\cAlgo\Logfiles\OHLCTestBot_Python.log"
    csharp_log = r"C:\Users\HMz\Documents\cAlgo\Data\cBots\OHLCTestBot\29639f65-52c0-4443-a8c7-b6511867444a\Backtesting\log.txt"
    output_file = r"C:\Users\HMz\Documents\cAlgo\Logfiles\rsi_test_results.txt"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=== RSI COMPARISON TEST RESULTS ===\n\n")
        
        # Extract H4 RSI values
        py_data = {}
        cs_data = {}
        
        with open(python_log, 'r', encoding='utf-8') as py_log:
            for line in py_log:
                if line.startswith('FINAL_IND|H4|'):
                    parts = line.strip().split('|')
                    if len(parts) >= 4:
                        time_str = parts[2]
                        if time_str.startswith('2025-12-04'):
                            continue
                        for part in parts[3:]:
                            if part.startswith('RSI='):
                                try:
                                    rsi_val = float(part.split('=')[1])
                                    py_data[time_str] = rsi_val
                                    break
                                except:
                                    pass
        
        with open(csharp_log, 'r', encoding='utf-8') as cs_log:
            for line in cs_log:
                if 'FINAL_IND|H4|' in line:
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
                                        cs_data[time_str] = rsi_val
                                        break
                                    except:
                                        pass
        
        common_times = sorted(set(py_data.keys()) & set(cs_data.keys()))
        f.write(f"Python H4 entries: {len(py_data)}\n")
        f.write(f"C# H4 entries: {len(cs_data)}\n")
        f.write(f"Common entries: {len(common_times)}\n\n")
        
        mismatches = []
        for time_str in common_times:
            py_rsi = py_data[time_str]
            cs_rsi = cs_data[time_str]
            diff = abs(py_rsi - cs_rsi)
            if diff > 0.01:
                mismatches.append((time_str, py_rsi, cs_rsi, diff))
        
        f.write(f"RSI Mismatches (>0.01): {len(mismatches)}\n\n")
        
        if mismatches:
            avg_diff = sum(m[3] for m in mismatches) / len(mismatches)
            max_diff = max(m[3] for m in mismatches)
            f.write(f"Average RSI diff: {avg_diff:.8f}\n")
            f.write(f"Max RSI diff: {max_diff:.8f}\n\n")
            
            f.write("First 10 mismatches:\n")
            for time_str, py_rsi, cs_rsi, diff in mismatches[:10]:
                f.write(f"  {time_str}: Py={py_rsi:.5f}, C#={cs_rsi:.5f}, Diff={diff:.8f}\n")

if __name__ == "__main__":
    main()
