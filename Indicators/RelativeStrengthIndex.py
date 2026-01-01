"""
Relative Strength Index (RSI) Indicator
Ported from cTrader.Automate.Indicators
"""
import math
from Api.IIndicator import IIndicator
from Api.DataSeries import DataSeries
from Indicators.ExponentialMovingAverage import ExponentialMovingAverage


class RelativeStrengthIndex(IIndicator):
    """
    Relative Strength Index (RSI)
    
    RSI is a momentum oscillator that measures the speed and magnitude of price changes.
    It oscillates between 0 and 100, with readings above 70 indicating overbought conditions
    and readings below 30 indicating oversold conditions.
    
    Formula:
        RSI = 100 - (100 / (1 + RS))
        where RS = Average Gain / Average Loss
        
    The averages are calculated using Exponential Moving Average with period (2 * periods - 1)
    """
    
    def __init__(
        self,
        source: DataSeries,
        periods: int = 14
    ):
        """
        Initialize Relative Strength Index
        
        Args:
            source: Input data series (typically close prices)
            periods: Number of periods for RSI calculation (default: 14)
        """
        self.source: DataSeries = source
        self.periods: int = periods
        
        # Get parent and size for DataSeries
        parent_bars = self.source._parent if hasattr(self.source, '_parent') else self.source.parent
        size = getattr(parent_bars, 'size', 1000) if hasattr(parent_bars, 'size') else 1000
        
        # Create internal DataSeries for gains and losses
        self._gains = DataSeries(parent_bars, size)
        self._losses = DataSeries(parent_bars, size)
        
        # Create result DataSeries
        self.result = DataSeries(parent_bars, size)
        
        # Create EMAs for gains and losses
        # cTrader uses period = 2 * periods - 1
        ema_periods = 2 * periods - 1
        self._ema_gain = ExponentialMovingAverage(self._gains, ema_periods, 0)
        # Wilder's smoothing state
        self.avg_gain = 0.0
        self.avg_loss = 0.0
        
    def initialize(self) -> None:
        """Initialize the indicator (required by IIndicator interface)"""
        # EMAs are already created in __init__
        pass
        
    def calculate(self, index: int) -> None:
        """
        Calculate RSI for the given index
        
        Args:
            index: The bar index to calculate
        """
        count = len(self.source.data)
        if count == 0 or index < 1:  # Need at least 2 bars
            return
            
        if index >= count:
            return
        
        # Get current and previous price
        current_price = self.source.data[index]
        prev_price = self.source.data[index - 1]
        
        if current_price is None or prev_price is None or math.isnan(current_price) or math.isnan(prev_price):
            return
        
        # Calculate gains and losses
        gain = max(0.0, current_price - prev_price)
        loss = max(0.0, prev_price - current_price)
        self._gains.data[index] = gain
        self._losses.data[index] = loss
        
        # Wilder's Smoothing implementation for RSI
        # RSI(N) starts at bar N (index N if starting at 0)
        if index < self.periods:
            return
            
        if index == self.periods:
            # Step 1: Initialize with Simple Moving Average of first N gains/losses
            sum_gains = 0.0
            sum_losses = 0.0
            valid_bars = 0
            for i in range(1, index + 1):
                g = self._gains.data[i]
                l = self._losses.data[i]
                if not math.isnan(g) and not math.isnan(l):
                    sum_gains += g
                    sum_losses += l
                    valid_bars += 1
            
            if valid_bars > 0:
                self.avg_gain = sum_gains / self.periods
                self.avg_loss = sum_losses / self.periods
        else:
            # Step 2: Use Wilder's Smoothing formula
            # S(i) = (S(i-1) * (N-1) + Current) / N
            prev_avg_gain = getattr(self, 'avg_gain', 0.0)
            prev_avg_loss = getattr(self, 'avg_loss', 0.0)
            
            self.avg_gain = (prev_avg_gain * (self.periods - 1) + gain) / self.periods
            self.avg_loss = (prev_avg_loss * (self.periods - 1) + loss) / self.periods

        # Calculate RSI
        if self.avg_loss == 0.0:
            self.result.data[index] = 100.0 if self.avg_gain > 0 else 50.0
        else:
            rs = self.avg_gain / self.avg_loss
            self.result.data[index] = 100.0 - (100.0 / (1.0 + rs))
    
    def __getitem__(self, index: int) -> float:
        """Allow array-style access to results"""
        return self.result[index]


# end of file
