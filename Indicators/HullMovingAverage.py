from Api.IIndicator import IIndicator
from Api.DataSeries import DataSeries
from Indicators.MovingAverage import MovingAverage
import math


class HullMovingAverage(MovingAverage, IIndicator):
    """
    Hull Moving Average (HMA) indicator.
    1:1 port from cTrader.
    """
    def __init__(self, source: DataSeries, periods: int = 14):
        super().__init__(source, periods)
        self._wma1 = None
        self._wma2 = None
        self._diff_series = None
        self._hma_wma = None

    def initialize(self) -> None:
        from Indicators.WeightedMovingAverage import WeightedMovingAverage
        
        self._wma1 = WeightedMovingAverage(self.source, int(self.periods / 2))
        self._wma1.initialize()
        
        self._wma2 = WeightedMovingAverage(self.source, self.periods)
        self._wma2.initialize()
        
        # Internal series for (2 * WMA1 - WMA2)
        # Set is_indicator_result=True to allow using __setitem__ with absolute indices
        self._diff_series = DataSeries(self.source._parent, self.result._size, is_indicator_result=True)
        # This series is owned by HMA for calculation purposes
        self._diff_series.set_owner_indicator(self) 
        
        self._hma_wma = WeightedMovingAverage(self._diff_series, int(math.sqrt(self.periods)))
        self._hma_wma.initialize()

    def calculate(self, index: int) -> None:
        """
        1:1 port from cTrader HullMovingAverage.Calculate(int index)
        """
        v1 = self._wma1.result[index]
        v2 = self._wma2.result[index]
        
        if math.isnan(v1) or math.isnan(v2):
            self.result[index] = float('nan')
            return
            
        self._diff_series[index] = 2.0 * v1 - v2
        
        # Trigger HMA WMA calculation
        self.result[index] = self._hma_wma.result[index]
