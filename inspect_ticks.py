import gzip
import struct
import os
from datetime import datetime, timedelta
import pytz

cache_path = r"C:\Users\HMz\AppData\Roaming\Spotware\Cache\pepperstone\BacktestingCache\V1\demo_19011fd1\AUDNZD\t1\20250722.zticks"

def inspect():
    if not os.path.exists(cache_path):
        print("File not found!")
        return

    print(f"Inspecting {cache_path}")
    
    with gzip.open(cache_path, "rb") as f:
        ba = f.read()
    
    print(f"File size: {len(ba)} bytes")
    
    source_ndx = 0
    count = 0
    # Read first 10 ticks
    while source_ndx < len(ba) and count < 10:
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
        
        print(f"#{count}: TS={ts_raw} ({dt}), BidRaw={bid_raw}, AskRaw={ask_raw}")
        count += 1

inspect()
