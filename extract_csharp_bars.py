"""
Extract C# Logged Bars from console output and save to CSV.
Parses lines starting with FINAL_BAR.
"""
# Primary source: cTrader GUI Log file provided by user
# "C:\Users\HMz\Documents\cAlgo\Data\cBots\OHLCTestBot\ae1d37c1-c662-478c-bd96-319a755b6b13\Backtesting\log.txt"
INPUT_LOG = r"C:\Users\HMz\Documents\cAlgo\Data\cBots\OHLCTestBot\ae1d37c1-c662-478c-bd96-319a755b6b13\Backtesting\log.txt"
OUTPUT_DIR = r"C:\Users\HMz\Documents\cAlgo\Logfiles"

import os

def extract_bars():
    input_file = INPUT_LOG
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    # Files to write
    out_m1 = os.path.join(OUTPUT_DIR, "OHLC_Test_CSharp_M1.csv")
    out_h1 = os.path.join(OUTPUT_DIR, "OHLC_Test_CSharp_H1.csv")
    out_h4 = os.path.join(OUTPUT_DIR, "OHLC_Test_CSharp_H4.csv")
    
    # Header: Time,Open,High,Low,Close,Volume
    header = "Time,Open,High,Low,Close,Volume\n"
    
    m1_lines = []
    h1_lines = []
    h4_lines = []
    
    # Use utf-8 with error handling, or try utf-16
    content = ""
    try:
        # Check for BOM
        with open(input_file, 'rb') as f:
            start = f.read(4)
        
        encoding = 'utf-8' # default
        if start.startswith(b'\xff\xfe'):
            encoding = 'utf-16-le'
        elif start.startswith(b'\xfe\xff'):
            encoding = 'utf-16-be'
        
        print(f"Detected/Using encoding: {encoding}")
        with open(input_file, 'r', encoding=encoding, errors='ignore') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Failed to read input file: {e}")
        return

    count = 0
    for line in lines:
        if "FINAL_BAR" in line:
            # Format: ... | Info | FINAL_BAR|TF|Time|O|H|L|C|V
            if "FINAL_BAR|" in line:
                parts = line.split("FINAL_BAR|")
                payload_str = parts[-1].strip()
                payload = payload_str.split('|')
                if len(payload) >= 7:
                    tf = payload[0]
                    csv_line = ",".join(payload[1:7])  # Time, O, H, L, C, V
                    if tf == "M1":
                        m1_lines.append(csv_line)
                    elif tf == "H1":
                        h1_lines.append(csv_line)
                    elif tf == "H4":
                        h4_lines.append(csv_line)
                    count += 1
                
    print(f"Extracted {count} final bars total.")
    print(f"M1: {len(m1_lines)}, H1: {len(h1_lines)}, H4: {len(h4_lines)}")
    
    # Sort by time to ensure order
    m1_lines.sort()
    h1_lines.sort()
    h4_lines.sort()

    with open(out_m1, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write('\n'.join(m1_lines))
        f.write('\n')
        
    with open(out_h1, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write('\n'.join(h1_lines))
        f.write('\n')

    with open(out_h4, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write('\n'.join(h4_lines))
        f.write('\n')
        
    print("Files written.")

if __name__ == "__main__":
    extract_bars()
