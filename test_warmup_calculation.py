"""
Test script to verify warmup period calculation for H4 RSI
Calculates the required warmup period manually
"""
from datetime import datetime

def test_warmup_calculation():
    """Calculate warmup period needed for H4 RSI with internal EMAs"""
    
    print("=== RSI Warmup Calculation Test (H4) ===")
    print()
    
    # H4 timeframe
    h4_seconds = 14400  # 4 hours
    rsi_periods = 20
    
    # RSI warmup
    rsi_warmup_seconds = (rsi_periods + 1) * h4_seconds
    rsi_warmup_days = rsi_warmup_seconds / 86400
    rsi_warmup_hours = rsi_warmup_seconds / 3600
    
    print(f"RSI Configuration:")
    print(f"  Periods: {rsi_periods}")
    print(f"  Timeframe: {h4_seconds}s (H4 = 4 hours)")
    print(f"  Warmup needed: {rsi_warmup_days:.2f} days ({rsi_warmup_hours:.1f} hours)")
    print()
    
    # Internal EMA warmup (2 * periods - 1)
    ema_periods = 2 * rsi_periods - 1  # 39 periods
    ema_warmup_seconds = (ema_periods + 1) * h4_seconds
    ema_warmup_days = ema_warmup_seconds / 86400
    ema_warmup_hours = ema_warmup_seconds / 3600
    
    print(f"Internal EMA Configuration (for Gains/Losses):")
    print(f"  Periods: {ema_periods} (2 * {rsi_periods} - 1)")
    print(f"  Timeframe: {h4_seconds}s (H4 = 4 hours)")
    print(f"  Warmup needed: {ema_warmup_days:.2f} days ({ema_warmup_hours:.1f} hours)")
    print()
    
    # Maximum warmup needed
    max_warmup_seconds = max(rsi_warmup_seconds, ema_warmup_seconds)
    max_warmup_days = max_warmup_seconds / 86400
    max_warmup_hours = max_warmup_seconds / 3600
    
    print(f"=== Summary ===")
    print(f"RSI warmup: {rsi_warmup_days:.2f} days ({rsi_warmup_hours:.1f} hours)")
    print(f"EMA warmup: {ema_warmup_days:.2f} days ({ema_warmup_hours:.1f} hours)")
    print(f"Max warmup needed: {max_warmup_days:.2f} days ({max_warmup_hours:.1f} hours)")
    print()
    
    # Compare with current WarmupStart setting
    warmup_start = datetime.strptime("24.11.2025", "%d.%m.%Y")
    backtest_start = datetime.strptime("01.12.2025", "%d.%m.%Y")
    warmup_days = (backtest_start - warmup_start).days
    warmup_hours = warmup_days * 24
    
    print(f"=== Current Configuration ===")
    print(f"WarmupStart: {warmup_start.strftime('%d.%m.%Y')}")
    print(f"BacktestStart: {backtest_start.strftime('%d.%m.%Y')}")
    print(f"Warmup duration: {warmup_days} days ({warmup_hours} hours)")
    print()
    
    if max_warmup_hours <= warmup_hours:
        print(f"[OK] Warmup phase is SUFFICIENT ({warmup_hours:.1f}h >= {max_warmup_hours:.1f}h needed)")
        print(f"   Margin: {warmup_hours - max_warmup_hours:.1f} hours ({(warmup_hours - max_warmup_hours) / 24:.2f} days)")
    else:
        print(f"[ERROR] Warmup phase is INSUFFICIENT ({warmup_hours:.1f}h < {max_warmup_hours:.1f}h needed)")
        print(f"   Need to increase WarmupStart by {(max_warmup_hours - warmup_hours) / 24:.1f} days")
        print(f"   Suggested WarmupStart: {(warmup_start - datetime(2025, 11, 24)).days - int((max_warmup_hours - warmup_hours) / 24)} days earlier")

if __name__ == "__main__":
    test_warmup_calculation()
