import os
from datetime import datetime
import pytz

gui_log = r"C:\Users\HMz\Documents\cAlgo\Data\cBots\OHLCTestBot\ae1d37c1-c662-478c-bd96-319a755b6b13\Backtesting\log.txt"

def check_gui_dupes():
    ticks = []
    with open(gui_log, "r", encoding="utf-8") as f:
        for line in f:
            if "," in line and "|" in line:
                try:
                    parts = line.split("|")
                    if len(parts) < 3: continue
                    payload = parts[-1].strip().split(",")
                    if len(payload) < 3: continue
                    
                    time_str = payload[0].strip()
                    if len(time_str) < 19: continue
                    
                    # Store as tuple (TimeStr, Bid, Ask)
                    ticks.append((time_str, payload[1], payload[2]))
                except:
                    continue
    
    total = len(ticks)
    unique = len(set(ticks))
    print(f"Total lines in log: {total}")
    print(f"Unique (Time, Bid, Ask) ticks: {unique}")
    print(f"Duplicates: {total - unique}")

check_gui_dupes()
