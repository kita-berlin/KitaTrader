import csv
import os

cs_log = r"C:\Users\HMz\Documents\cAlgo\Logfiles\Kanga2 _4.csv"
py_log = r"C:\Users\HMz\Documents\cAlgo\Logfiles\Kanga2 _5.csv"

def load_keys(filepath):
    trades = []
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        start_idx = 1 if lines and lines[0].strip().startswith('sep=') else 0
        reader = csv.DictReader(lines[start_idx:])
        for row in reader:
            if not row or not any(row.values()):
                continue
            symbol = (row.get('Symbol') or '').strip()
            open_date = (row.get('OpenDate') or '').strip()
            open_price = (row.get('OpenPrice') or '').strip()
            lots = (row.get('Lots') or '').strip()
            key = f"{symbol}_{open_date}_{open_price}_{lots}"
            trades.append({
                'key': key,
                'symbol': symbol,
                'open_date': open_date,
                'open_price': open_price,
                'lots': lots,
                'row': row
            })
    return trades

cs_trades = load_keys(cs_log)
py_trades = load_keys(py_log)

print(f"C# trades: {len(cs_trades)}")
print(f"Python trades: {len(py_trades)}")

cs_keys = {t['key'] for t in cs_trades}
py_keys = {t['key'] for t in py_trades}

print(f"\nC# unique keys: {len(cs_keys)}")
print(f"Python unique keys: {len(py_keys)}")
print(f"Common keys: {len(cs_keys & py_keys)}")
print(f"Only in C#: {len(cs_keys - py_keys)}")
print(f"Only in Python: {len(py_keys - cs_keys)}")

print("\nFirst 10 C# keys:")
for i, key in enumerate(sorted(list(cs_keys))[:10]):
    print(f"  {i+1}. {key}")

print("\nFirst 10 Python keys:")
for i, key in enumerate(sorted(list(py_keys))[:10]):
    print(f"  {i+1}. {key}")

# Check for differences in first few trades
print("\n=== Comparing first 5 trades ===")
for i in range(min(5, len(cs_trades), len(py_trades))):
    cs = cs_trades[i]
    py = py_trades[i]
    print(f"\nTrade {i+1}:")
    print(f"  C# key: {cs['key']}")
    print(f"  Py key: {py['key']}")
    print(f"  Match: {cs['key'] == py['key']}")
    if cs['key'] != py['key']:
        print(f"  C#: Symbol='{cs['symbol']}', Date='{cs['open_date']}', Price='{cs['open_price']}', Lots='{cs['lots']}'")
        print(f"  Py: Symbol='{py['symbol']}', Date='{py['open_date']}', Price='{py['open_price']}', Lots='{py['lots']}'")

