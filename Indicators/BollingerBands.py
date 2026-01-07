from Api.IIndicator import IIndicator
from Api.DataSeries import DataSeries
from Indicators.StandardIndicator import StandardIndicator
from Api.KitaApiEnums import MovingAverageType
import math


class BollingerBands(StandardIndicator, IIndicator):
    """
    Bollinger Bands indicator.
    1:1 port from cTrader.
    """
    def __init__(self, source: DataSeries, periods: int = 20, standard_deviations: float = 2.0, ma_type: MovingAverageType = MovingAverageType.Simple):
        super().__init__(source, periods)
        self.standard_deviations = standard_deviations
        self.ma_type = ma_type
        
        # Bollinger Bands has 3 outputs. All must be indicator results.
        self.main = self.result
        self.top = self.create_data_series(is_indicator_result=True)
        self.bottom = self.create_data_series(is_indicator_result=True)
        
        # Indicators for internal calculation
        self._ma_indicator = None
        self._sd_indicator = None

    def initialize(self) -> None:
        """Initialize internal indicators"""
        from Indicators.SimpleMovingAverage import SimpleMovingAverage
        from Indicators.ExponentialMovingAverage import ExponentialMovingAverage
        from Indicators.WeightedMovingAverage import WeightedMovingAverage
        from Indicators.StandardDeviation import StandardDeviation
        
        if self.ma_type == MovingAverageType.Simple:
            self._ma_indicator = SimpleMovingAverage(self.source, self.periods)
        elif self.ma_type == MovingAverageType.Exponential:
            self._ma_indicator = ExponentialMovingAverage(self.source, self.periods)
        elif self.ma_type == MovingAverageType.Weighted:
            self._ma_indicator = WeightedMovingAverage(self.source, self.periods)
        else:
            self._ma_indicator = SimpleMovingAverage(self.source, self.periods)
            
        self._ma_indicator.initialize()
        
        self._sd_indicator = StandardDeviation(self.source, self.periods)
        self._sd_indicator.initialize()

    def calculate(self, index: int) -> None:
        """
        1:1 port from cTrader BollingerBands.Calculate(int index)
        """
        ma_val = self._ma_indicator.result[index]
        sd_val = self._sd_indicator.result[index]
        
        if math.isnan(ma_val) or math.isnan(sd_val):
            self.main[index] = float('nan')
            self.top[index] = float('nan')
            self.bottom[index] = float('nan')
            return
            
        self.main[index] = ma_val
        self.top[index] = ma_val + (self.standard_deviations * sd_val)
        self.bottom[index] = ma_val - (self.standard_deviations * sd_val)
