"""
Quick Verification Test - Run individual tests manually
Usage: python quick_verify.py <season> <timeframe>
Example: python quick_verify.py summer h1
"""
import sys
import os

if len(sys.argv) != 3:
    print("Usage: python quick_verify.py <season> <timeframe>")
    print("Seasons: summer, winter")
    print("Timeframes: ticks, m1, h1, h3, d1")
    sys.exit(1)

season = sys.argv[1].lower()
timeframe = sys.argv[2].lower()

# Configuration
CONFIGS = {
    "summer": {
        "start": "22.07.2025",
        "end": "25.07.2025",
        "start_cs": "22/07/2025",
        "end_cs": "25/07/2025"
    },
    "winter": {
        "start": "15.01.2025",
        "end": "18.01.2025",
        "start_cs": "15/01/2025",
        "end_cs": "18/01/2025"
    }
}

TIMEFRAMES = {
    "ticks": {"seconds": 0, "period": "m1", "name": "Ticks"},
    "m1": {"seconds": 60, "period": "m1", "name": "M1"},
    "h1": {"seconds": 3600, "period": "h1", "name": "H1"},
    "h3": {"seconds": 10800, "period": "h3", "name": "H3"},
    "d1": {"seconds": 86400, "period": "d1", "name": "D1"}
}

if season not in CONFIGS:
    print(f"Invalid season: {season}")
    sys.exit(1)

if timeframe not in TIMEFRAMES:
    print(f"Invalid timeframe: {timeframe}")
    sys.exit(1)

config = CONFIGS[season]
tf = TIMEFRAMES[timeframe]

print(f"\n{'='*80}")
print(f"Verification Test: {season.upper()} - {tf['name']}")
print(f"{'='*80}\n")

print(f"Date Range: {config['start']} to {config['end']}")
print(f"Timeframe: {tf['name']} ({tf['seconds']}s)")
print(f"Period: {tf['period']}")
print()

# Print configuration commands
print("Run these commands manually:")
print()
print("1. Update MainConsole.py dates:")
print(f"   AllDataStartUtc: {config['start']}")
print(f"   AllDataEndUtc: {config['end']}")
print(f"   BacktestStartUtc: {config['start']}")
print(f"   BacktestEndUtc: {config['end']}")
print()
print("2. Update PriceVerifyBot.py:")
print(f"   request_bars({tf['seconds']})")
print(f"   get_bars({tf['seconds']})")
print(f"   Log file: PriceVerify_Python_{season.capitalize()}_{tf['name']}.csv")
print()
print("3. Update run_cli_verification.bat:")
print(f"   --start={config['start_cs']}")
print(f"   --end={config['end_cs']}")
print(f"   --period={tf['period']}")
print(f"   Output: PriceVerify_CSharp_{season.capitalize()}_{tf['name']}.txt")
print()
print("4. Run:")
print("   .\\run_cli_verification.bat")
print("   python MainConsole.py")
print()
print("5. Update compare_logs.py:")
print(f"   C#: PriceVerify_CSharp_{season.capitalize()}_{tf['name']}.txt")
print(f"   Python: PriceVerify_Python_{season.capitalize()}_{tf['name']}.csv")
print()
print("6. Compare:")
print("   python compare_logs.py")
print()
