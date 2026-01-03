import os
import gzip

base = r"C:\Users\HMz\AppData\Roaming\Spotware\Cache\Spotware\BacktestingCache\V1\demo_19011fd1\AUDNZD\t1"
files = [f for f in os.listdir(base) if f.endswith(".zticks")]
files.sort()

total = 0
for f in files:
    date = f.split(".")[0]
    # Filter 12/01 to 12/04
    if date < "20251201" or date > "20251204":
        continue
        
    path = os.path.join(base, f)
    data = gzip.open(path, "rb").read()
    count = len(data) // 24
    total += count
    print(f"{f}: {count}")

print(f"Total Ticks (12/01 to 12/04): {total}")
