"""
Test RSI calculation with exact EMA values
Verify that the logged EMA values produce the logged RSI value
"""
import math

# Test case from log: 2025-11-30 22:00:00
# Logged: RSI=12.58210, EMA_Gain=0.00013000, EMA_Loss=0.00087000
ema_gain = 0.00013000
ema_loss = 0.00087000

# Calculate RSI from EMA values
if ema_loss == 0.0:
    num3 = float('inf') if ema_gain > 0.0 else float('-inf') if ema_gain < 0.0 else float('nan')
else:
    num3 = ema_gain / ema_loss

rsi = 100.0 - 100.0 / (1.0 + num3)

print(f"EMA Gain: {ema_gain}")
print(f"EMA Loss: {ema_loss}")
print(f"num3 (ema_gain / ema_loss): {num3}")
print(f"Calculated RSI: {rsi:.10f}")
print(f"Logged RSI: 12.58210")
print(f"Difference: {abs(rsi - 12.58210):.10f}")

# Test with more precision
print("\n=== Testing with higher precision ===")
ema_gain_exact = 0.00013  # Without trailing zeros
ema_loss_exact = 0.00087

num3_exact = ema_gain_exact / ema_loss_exact
rsi_exact = 100.0 - 100.0 / (1.0 + num3_exact)

print(f"EMA Gain (exact): {ema_gain_exact}")
print(f"EMA Loss (exact): {ema_loss_exact}")
print(f"num3: {num3_exact:.15f}")
print(f"Calculated RSI: {rsi_exact:.10f}")
print(f"Logged RSI: 12.58210")
print(f"Difference: {abs(rsi_exact - 12.58210):.10f}")

# Try to find the exact EMA values that produce 12.58210
print("\n=== Reverse engineering EMA values ===")
target_rsi = 12.58210
# RSI = 100.0 - 100.0 / (1.0 + num3)
# 100.0 - RSI = 100.0 / (1.0 + num3)
# (100.0 - RSI) / 100.0 = 1 / (1.0 + num3)
# 1.0 + num3 = 100.0 / (100.0 - RSI)
# num3 = 100.0 / (100.0 - RSI) - 1.0
num3_target = 100.0 / (100.0 - target_rsi) - 1.0
print(f"Target num3: {num3_target:.15f}")

# num3 = ema_gain / ema_loss
# If we assume ema_loss = 0.00087, then ema_gain = num3 * ema_loss
ema_loss_assumed = 0.00087
ema_gain_calculated = num3_target * ema_loss_assumed
print(f"Assuming EMA Loss = {ema_loss_assumed}")
print(f"Calculated EMA Gain = {ema_gain_calculated:.15f}")
print(f"Logged EMA Gain = 0.00013000")
print(f"Difference: {abs(ema_gain_calculated - 0.00013000):.15f}")

# Try with ema_gain = 0.00013
ema_gain_assumed = 0.00013
ema_loss_calculated = ema_gain_assumed / num3_target
print(f"\nAssuming EMA Gain = {ema_gain_assumed}")
print(f"Calculated EMA Loss = {ema_loss_calculated:.15f}")
print(f"Logged EMA Loss = 0.00087000")
print(f"Difference: {abs(ema_loss_calculated - 0.00087000):.15f}")
