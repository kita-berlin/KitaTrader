import gzip
import struct
import pytz
import os
from datetime import datetime

# Paths
cache_file = r"C:\Users\HMz\AppData\Roaming\Spotware\Cache\Spotware\BacktestingCache\V1\demo_19011fd1\AUDNZD\t1\20251201.zticks"
gui_log = r"C:\Users\HMz\Documents\cAlgo\Data\cBots\OHLCTestBot\ae1d37c1-c662-478c-bd96-319a755b6b13\Backtesting\log.txt"

def load_cache_ticks():
    ticks = []
    with gzip.open(cache_file, "rb") as f:
        ba = f.read()
    
    ndx = 0
    while ndx < len(ba):
        ts_ms = struct.unpack_from("<q", ba, ndx)[0]
        ndx += 8
        bid = struct.unpack_from("<q", ba, ndx)[0] / 100000.0
        ndx += 8
        ask = struct.unpack_from("<q", ba, ndx)[0] / 100000.0
        ndx += 8
        ticks.append((ts_ms, bid, ask))
    return ticks

def load_gui_ticks():
    ticks = []
    # Format: HH:mm:ss.fff | Info | YYYY-MM-DD HH:mm:ss.fff,Bid,Ask,Spread
    # Example: 01.12.2025 00:00:00.521 | Info | 2025-12-01 00:00:00.521,1.14208,1.14217,0.00009
    with open(gui_log, "r", encoding="utf-8") as f:
        for line in f:
            if "," in line and "|" in line:
                try:
                    parts = line.split("|")
                    if len(parts) < 3: continue
                    payload = parts[-1].strip().split(",")
                    if len(payload) < 3: continue
                    
                    time_str = payload[0].strip()
                    # Check if it looks like a tick time
                    if len(time_str) < 19: continue
                    
                    dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S.%f")
                    ts_ms = int(dt.timestamp() * 1000)
                    bid = float(payload[1])
                    ask = float(payload[2])
                    ticks.append((ts_ms, bid, ask))
                except:
                    continue
    return ticks

print("Loading cache ticks...")
cache_ticks = load_cache_ticks()
print(f"Loaded {len(cache_ticks)} ticks from cache.")

print("Loading GUI ticks...")
gui_ticks = load_gui_ticks()
print(f"Loaded {len(gui_ticks)} ticks from GUI log.")

# Compare counts
print(f"Difference: {len(gui_ticks) - len(cache_ticks)}")

# Check first 10
print("\nFirst 5 cache ticks:")
for t in cache_ticks[:5]: print(t)

print("\nFirst 5 GUI ticks:")
for t in gui_ticks[:5]: print(t)
