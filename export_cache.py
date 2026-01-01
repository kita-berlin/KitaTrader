from datetime import datetime
from BrokerProvider.QuoteCtraderCache import QuoteCtraderCache
from Api.Symbol import Symbol
from Api.KitaApi import KitaApi
from Robots.PriceVerifyBot import QuoteCtraderCacheTick

# Dummy API and Symbol to satisfy QuoteCtraderCache
class MockApi(KitaApi):
    def resolve_env_variables(self, path):
        return path

class MockSymbol(Symbol):
    def __init__(self, name):
        self.name = name
        self.point_size = 0.00001
        self.digits = 5

api = MockApi()
symbol = MockSymbol("AUDNZD")

# Path to the cache user specified
cache_path = r"C:\Users\HMz\AppData\Roaming\Spotware\Cache\pepperstone\BacktestingCache\V1\demo_19011fd1"

# Initialize Provider
provider = QuoteCtraderCache(0, cache_path)
provider.init_symbol(api, symbol)

# Open CSV for writing
with open("AUDNZD_Local.csv", "w", encoding='utf-8') as f:
    # Header for cTrader CSV?
    # cTrader generic CSV format: Date, Time, Open, High, Low, Close, Volume
    # For Ticks: Date, Time, Bid, Ask
    # Let's try standard format: yyyy.MM.dd,HH:mm:ss.fff,Bid,Ask
    # Header might be needed or not. Safest is no header or standard header.
    # We will try NO header first, or check docs.
    # Actually most imports require Date,Time,Bid,Ask header or mapping.
    # Let's write header.
    f.write("Date,Time,Bid,Ask\n")
    
    # Load 22nd, 23rd
    days = [datetime(2025, 7, 22), datetime(2025, 7, 23), datetime(2025, 7, 24)]
    
    count = 0
    for day in days:
        err, dt, bars = provider.get_day_at_utc(day)
        if err == "":
            print(f"Exporting {day.date()}...")
            count_day = 0
            # bars.open_times is array of datetimes
            for i in range(bars.count):
                t = bars.open_times.data[i]
                b = bars.open_bids.data[i]
                a = bars.open_asks.data[i]
                
                # Debug first 5 ticks
                if count_day < 5:
                    print(f"Tick #{count_day}: Time={t}, Bid={b:.5f}, Ask={a:.5f}")
                
                # Format: 2025.07.22,00:00:00.846,1.09355,1.09364
                date_str = t.strftime("%d/%m/%Y")
                time_str = t.strftime("%H:%M:%S.%f")[:-3]
                
                f.write(f"{date_str} {time_str},{b:.5f},{a:.5f}\n")
                count += 1
                count_day += 1
    print(f"Exported {count} ticks.")
