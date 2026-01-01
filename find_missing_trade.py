import csv

cs_log = r"C:\Users\HMz\Documents\cAlgo\Logfiles\Kanga2 _4.csv"
py_log = r"C:\Users\HMz\Documents\cAlgo\Logfiles\Kanga2 _5.csv"

def load_trades(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    start = 1 if lines[0].strip().startswith('sep=') else 0
    reader = csv.DictReader(lines[start:])
    trades = []
    for row in reader:
        if not row or not any(row.values()):
            continue
        clean_row = {k: (v or '').strip() for k, v in row.items()}
        # Skip footer lines (lines that don't have a valid Number or have invalid data)
        number = clean_row.get('Number', '')
        symbol = clean_row.get('Symbol', '')
        if not number or not number.isdigit() or not symbol or symbol == '':
            continue
        key = f"{clean_row.get('Symbol', '')}_{clean_row.get('OpenDate', '')}_{clean_row.get('OpenPrice', '')}_{clean_row.get('Lots', '')}_{number}"
        trades.append({
            'key': key,
            'number': number,
            'row': clean_row
        })
    return trades

cs_trades = load_trades(cs_log)
py_trades = load_trades(py_log)

cs_keys = {t['key'] for t in cs_trades}
py_keys = {t['key'] for t in py_trades}

only_cs = cs_keys - py_keys
only_py = py_keys - cs_keys

print(f"C# trades: {len(cs_trades)}")
print(f"Python trades: {len(py_trades)}")
print(f"Common: {len(cs_keys & py_keys)}")
print(f"Only in C#: {len(only_cs)}")
print(f"Only in Python: {len(only_py)}")

if only_cs:
    print(f"\nTrades only in C#:")
    for key in only_cs:
        trade = next(t for t in cs_trades if t['key'] == key)
        print(f"  Number: {trade['number']}, Key: {key}")
        print(f"    {trade['row']}")

if only_py:
    print(f"\nTrades only in Python:")
    for key in only_py:
        trade = next(t for t in py_trades if t['key'] == key)
        print(f"  Number: {trade['number']}, Key: {key}")
        print(f"    {trade['row']}")

# Check trade numbers
cs_numbers = sorted([int(t['number']) for t in cs_trades if t['number']])
py_numbers = sorted([int(t['number']) for t in py_trades if t['number']])
print(f"\nC# trade numbers: {cs_numbers}")
print(f"Python trade numbers: {py_numbers}")
missing_in_py = set(cs_numbers) - set(py_numbers)
missing_in_cs = set(py_numbers) - set(cs_numbers)
if missing_in_py:
    print(f"Trade numbers only in C#: {sorted(missing_in_py)}")
if missing_in_cs:
    print(f"Trade numbers only in Python: {sorted(missing_in_cs)}")

