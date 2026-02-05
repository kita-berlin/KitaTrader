"""
Test script to check if the warmup check logic works correctly
"""
from datetime import datetime
import pytz

# BacktestStart: 01.12.2025
backtest_start = datetime(2025, 12, 1, 0, 0, 0)
backtest_start_utc = pytz.UTC.localize(backtest_start)

# First H4 bar: 2025-11-30 22:00:00
first_bar_time = datetime(2025, 11, 30, 22, 0, 0)
first_bar_time_utc = pytz.UTC.localize(first_bar_time)

# Previous H4 bar (4 hours before): 2025-11-30 18:00:00
prev_bar_time = datetime(2025, 11, 30, 18, 0, 0)
prev_bar_time_utc = pytz.UTC.localize(prev_bar_time)

print(f"BacktestStartUtc: {backtest_start_utc}")
print(f"First H4 bar time: {first_bar_time_utc}")
print(f"Previous H4 bar time: {prev_bar_time_utc}")
print()
print(f"prev_bar_time < backtest_start: {prev_bar_time_utc < backtest_start_utc}")
print(f"first_bar_time >= backtest_start: {first_bar_time_utc >= backtest_start_utc}")
print()
print(f"Should set Gain/Loss=0.0: {prev_bar_time_utc < backtest_start_utc and first_bar_time_utc >= backtest_start_utc}")
