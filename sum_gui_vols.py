import os

gui_log = r"C:\Users\HMz\Documents\cAlgo\Data\cBots\OHLCTestBot\ae1d37c1-c662-478c-bd96-319a755b6b13\Backtesting\log.txt"

def sum_gui_vols():
    total_vol = 0
    count = 0
    with open(gui_log, "r", encoding="utf-8") as f:
        for line in f:
            if "FINAL_BAR|M1|" in line and "2025-12-01" in line:
                parts = line.split("|")
                # Format: FINAL_BAR|M1|Time|Open|High|Low|Close|Volume
                vol = int(parts[-1].strip())
                total_vol += vol
                count += 1
    
    print(f"Total M1 TickVolume for Dec 1st: {total_vol}")
    print(f"M1 Bar count: {count}")

sum_gui_vols()
