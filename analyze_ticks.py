import gzip
import struct
import os
from datetime import datetime, timedelta
import pytz

cache_path = r"C:\Users\HMz\AppData\Roaming\Spotware\Cache\pepperstone\BacktestingCache\V1\demo_19011fd1\AUDNZD\t1\20250722.zticks"

def analyze():
    if not os.path.exists(cache_path):
        print("File not found!")
        return

    print(f"Analyzing {cache_path}")
    
    with gzip.open(cache_path, "rb") as f:
        ba = f.read()
    
    source_ndx = 0
    count_00_01 = 0
    bid_updates_00_01 = 0
    ask_updates_00_01 = 0
    
    while source_ndx < len(ba):
        # Timestamp
        ts_raw = struct.unpack_from("<q", ba, source_ndx)[0]
        ts_ms = ts_raw / 1000.0
        dt = datetime.fromtimestamp(ts_ms, tz=pytz.UTC)
        source_ndx += 8
        
        # Bid
        bid_raw = struct.unpack_from("<q", ba, source_ndx)[0]
        source_ndx += 8
        
        # Ask
        ask_raw = struct.unpack_from("<q", ba, source_ndx)[0]
        source_ndx += 8
        
        # Check hour 00
        if dt.hour == 0:
            count_00_01 += 1
            if bid_raw != 0:
                bid_updates_00_01 += 1
            if ask_raw != 0:
                ask_updates_00_01 += 1
                
    print(f"Hour 00:00 - 01:00 Stats:")
    print(f"Total Tick Entries: {count_00_01}")
    print(f"Bid Updates (!= 0): {bid_updates_00_01}")
    print(f"Ask Updates (!= 0): {ask_updates_00_01}")
    print(f"Sum Updates: {bid_updates_00_01 + ask_updates_00_01}")

analyze()
