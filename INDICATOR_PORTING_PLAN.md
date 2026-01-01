# KitaTrader Indicator Porting Plan

## Overview
Port all 87 cTrader indicators from C# to Python and verify each with H1 bar data.

## Status Summary
- **Total Indicators**: 87
- **Already Ported**: 6 (7%)
- **Remaining**: 81 (93%)

## Already Ported ✅
1. BollingerBands.py ✅ **VERIFIED** (matches cTrader exactly)
2. SimpleMovingAverage.py ✅
3. StandardDeviation.py ✅
4. Vidya.py ✅
5. MovingAverage.py ✅
6. Indicators.py (base/helper)

## Priority 1: Most Common Trading Indicators (Next 10)
These are the most widely used indicators in trading strategies:

1. **ExponentialMovingAverage** - EMA, essential for many strategies
2. **RelativeStrengthIndex** - RSI, momentum indicator
3. **MovingAverageConvergenceDivergence** (MACD) - Trend following
4. **StochasticOscillator** - Momentum indicator
5. **AverageTrueRange** - ATR, volatility measure
6. **ParabolicSAR** - Trend indicator
7. **IchimokuKinkoHyo** - Comprehensive trend system
8. **CommodityChannelIndex** - CCI, momentum
9. **DirectionalMovementSystem** - ADX/DMI
10. **DonchianChannel** - Breakout indicator

## Priority 2: Additional Popular Indicators (Next 15)
11. WeightedMovingAverage
12. TriangularMovingAverage
13. HullMovingAverage
14. KaufmanAdaptiveMovingAverage
15. DoubleExponentialMovingAverage
16. TripleExponentialMovingAverage
17. Aroon
18. KeltnerChannels
19. Envelopes
20. OnBalanceVolume
21. MoneyFlowIndex
22. ChaikinMoneyFlow
23. WilliamsPctR
24. DeMarker
25. MomentumOscillator

## Priority 3: Specialized Indicators (Remaining 56)
All other indicators including:
- Oscillators (Awesome, Accelerator, Chaikin, etc.)
- Volume indicators
- Volatility indicators
- Regression indicators
- Fractal indicators
- Custom indicators

## Implementation Strategy

### Phase 1: Setup Testing Framework
Create an automated testing system that can:
1. Load H1 bars for a test period (e.g., July 10-20, 2025)
2. Initialize both C# and Python indicators
3. Compare outputs automatically
4. Generate pass/fail reports

### Phase 2: Port Priority 1 Indicators (10 indicators)
- Estimated time: 2-3 hours per indicator
- Total: 20-30 hours

### Phase 3: Port Priority 2 Indicators (15 indicators)
- Estimated time: 2-3 hours per indicator
- Total: 30-45 hours

### Phase 4: Port Priority 3 Indicators (56 indicators)
- Estimated time: 1.5-2 hours per indicator (simpler ones)
- Total: 84-112 hours

### Total Estimated Time: 134-187 hours (3-4 weeks full-time)

## Testing Approach

### Automated Test Template
```python
class IndicatorTest:
    def __init__(self, indicator_name):
        self.indicator_name = indicator_name
        
    def run_test(self):
        # 1. Load H1 bars (July 10-20, 2025)
        # 2. Initialize Python indicator
        # 3. Run C# backtest with indicator
        # 4. Compare outputs
        # 5. Report results
```

### Test Data
- **Period**: July 10-20, 2025 (10 days)
- **Timeframe**: H1 (hourly bars)
- **Symbol**: AUDNZD
- **Expected bars**: ~240 H1 bars

### Success Criteria
- OHLC values match (already verified ✅)
- Indicator values match within tolerance (0.00001)
- All bars produce valid indicator values
- No NaN or infinite values (except where expected)

## Immediate Next Steps

1. **Create Automated Test Framework** (2-3 hours)
   - Generic indicator test bot (Python)
   - Generic indicator test bot (C#)
   - Automated comparison script
   
2. **Port & Test First Priority 1 Indicator: EMA** (2-3 hours)
   - Port ExponentialMovingAverage.cs to Python
   - Create test
   - Verify match
   
3. **Continue with Priority 1 List** (18-27 hours)
   - One indicator at a time
   - Full verification for each

## Notes
- Some indicators depend on others (e.g., MACD uses EMA)
- Port dependencies first
- Maintain consistent naming conventions
- Document any cTrader-specific behaviors
- Keep test results for future reference

## Current Session Recommendation
Given the scope, I recommend:
1. ✅ Create the automated testing framework (DONE - we have BollingerBands test as template)
2. ⏳ Port the next 2-3 Priority 1 indicators (EMA, RSI, MACD)
3. ⏳ Verify they work correctly
4. 📋 Create a tracking spreadsheet for remaining indicators

This provides immediate value while establishing a pattern for the remaining work.
