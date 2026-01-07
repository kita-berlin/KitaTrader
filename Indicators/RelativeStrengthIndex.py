from Api.IIndicator import IIndicator
from Api.DataSeries import DataSeries
from Indicators.StandardIndicator import StandardIndicator
import math


class RelativeStrengthIndex(StandardIndicator, IIndicator):
    """
    Relative Strength Index (RSI) indicator.
    1:1 port from cTrader.
    """
    def __init__(self, source: DataSeries, periods: int = 14):
        super().__init__(source, periods)

    def calculate(self, index: int) -> None:
        """
        1:1 port from cTrader RelativeStrengthIndex.Calculate(int index)
        """
        if index < self.periods:
            self.result[index] = float('nan')
            return

        if index == self.periods:
            # First calculation: Simple average of gains/losses
            sum_gain = 0.0
            sum_loss = 0.0
            for i in range(1, self.periods + 1):
                diff = self.source[i] - self.source[i-1]
                if diff > 0:
                    sum_gain += diff
                else:
                    sum_loss -= diff
            
            avg_gain = sum_gain / self.periods
            avg_loss = sum_loss / self.periods
            
            # Use class attributes to store internal state
            self._rsi_avg_gain = avg_gain
            self._rsi_avg_loss = avg_loss
            self._rsi_last_idx = index
        else:
            # Subsequent calculations: Wilder's smoothing
            # Ensure we have state from previous index
            if not hasattr(self, '_rsi_avg_gain') or self._rsi_last_idx != index - 1:
                # Re-calculate or skip if missing (should be handled by iterative lazy_calculate)
                return 

            diff = self.source[index] - self.source[index-1]
            gain = max(diff, 0.0)
            loss = max(-diff, 0.0)
            
            # Wilder's Smoothing: (prev * (n-1) + current) / n
            self._rsi_avg_gain = (self._rsi_avg_gain * (self.periods - 1) + gain) / self.periods
            self._rsi_avg_loss = (self._rsi_avg_loss * (self.periods - 1) + loss) / self.periods
            self._rsi_last_idx = index
            
        if self._rsi_avg_loss == 0:
            self.result[index] = 100.0
        else:
            rs = self._rsi_avg_gain / self._rsi_avg_loss
            self.result[index] = 100.0 - (100.0 / (1.0 + rs))
