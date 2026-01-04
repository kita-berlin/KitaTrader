"""
Verify all OHLCV values for M1, M5, H1, H4 bars from Python generation
"""
import csv
from datetime import datetime

def verify_ohlcv(csv_file, timeframe):
    """Verify OHLCV values are present and reasonable"""
    print(f"\n{'='*80}")
    print(f"Verifying {timeframe} bars - OHLCV values")
    print(f"{'='*80}")
    
    bars = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                time = datetime.strptime(row['Time'], "%Y-%m-%d %H:%M:%S")
                bars.append({
                    'time': time,
                    'open': float(row['Open']) if row['Open'] else None,
                    'high': float(row['High']) if row['High'] else None,
                    'low': float(row['Low']) if row['Low'] else None,
                    'close': float(row['Close']) if row['Close'] else None,
                    'volume': int(row['Volume']) if row['Volume'] else None
                })
            except (ValueError, KeyError) as e:
                print(f"Error parsing row: {row}... Error: {e}")
    
    if not bars:
        print(f"  No bars found in {timeframe}")
        return
    
    print(f"Total bars: {len(bars)}")
    
    # Check first and last bars
    print(f"\nFirst bar: {bars[0]['time']}")
    print(f"  Open:   {bars[0]['open']}")
    print(f"  High:   {bars[0]['high']}")
    print(f"  Low:    {bars[0]['low']}")
    print(f"  Close:  {bars[0]['close']}")
    print(f"  Volume: {bars[0]['volume']}")
    
    print(f"\nLast bar: {bars[-1]['time']}")
    print(f"  Open:   {bars[-1]['open']}")
    print(f"  High:   {bars[-1]['high']}")
    print(f"  Low:    {bars[-1]['low']}")
    print(f"  Close:  {bars[-1]['close']}")
    print(f"  Volume: {bars[-1]['volume']}")
    
    # Verify OHLCV relationships
    errors = 0
    for i, bar in enumerate(bars):
        if bar['high'] is not None and bar['low'] is not None and bar['open'] is not None and bar['close'] is not None:
            # High should be >= Open, Low, Close
            if bar['high'] < bar['open'] or bar['high'] < bar['low'] or bar['high'] < bar['close']:
                errors += 1
                if errors <= 5:
                    print(f"  ERROR: Bar {i} at {bar['time']}: High ({bar['high']}) is not highest!")
            # Low should be <= Open, High, Close
            if bar['low'] > bar['open'] or bar['low'] > bar['high'] or bar['low'] > bar['close']:
                errors += 1
                if errors <= 5:
                    print(f"  ERROR: Bar {i} at {bar['time']}: Low ({bar['low']}) is not lowest!")
            # Volume should be >= 0
            if bar['volume'] is not None and bar['volume'] < 0:
                errors += 1
                if errors <= 5:
                    print(f"  ERROR: Bar {i} at {bar['time']}: Volume ({bar['volume']}) is negative!")
    
    if errors == 0:
        print(f"\n[OK] All {len(bars)} bars have valid OHLCV relationships")
    else:
        print(f"\n[ERROR] Found {errors} errors in OHLCV relationships")
    
    # Show sample of bars
    print(f"\nSample bars (first 5):")
    for i, bar in enumerate(bars[:5]):
        print(f"  {bar['time']}: O={bar['open']:.5f}, H={bar['high']:.5f}, L={bar['low']:.5f}, C={bar['close']:.5f}, V={bar['volume']}")

def main():
    log_dir = r"C:\Users\HMz\Documents\cAlgo\Logfiles"
    
    timeframes = ['M1', 'M5', 'H1', 'H4']
    
    for tf in timeframes:
        csv_file = f"{log_dir}\\OHLC_Test_Python_{tf}.csv"
        verify_ohlcv(csv_file, tf)

if __name__ == '__main__':
    main()
