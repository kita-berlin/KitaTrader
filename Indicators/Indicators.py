"""
Indicators factory class - stub for testing
"""
class Indicators:
    def __init__(self, api=None, bot=None):
        self._api = api or bot
        self._created_indicators = []
    
    def simple_moving_average(self, source, periods):
        from Indicators.SimpleMovingAverage import SimpleMovingAverage
        indicator = SimpleMovingAverage(source, periods)
        indicator.initialize()
        self._created_indicators.append(indicator)
        return indicator

    def exponential_moving_average(self, source, periods, shift=0):
        from Indicators.ExponentialMovingAverage import ExponentialMovingAverage
        indicator = ExponentialMovingAverage(source, periods, shift)
        indicator.initialize()
        self._created_indicators.append(indicator)
        return indicator

    def weighted_moving_average(self, source, periods, shift=0):
        from Indicators.WeightedMovingAverage import WeightedMovingAverage
        indicator = WeightedMovingAverage(source, periods, shift)
        indicator.initialize()
        self._created_indicators.append(indicator)
        return indicator
        
    def hull_moving_average(self, source, periods):
        from Indicators.HullMovingAverage import HullMovingAverage
        indicator = HullMovingAverage(source, periods)
        indicator.initialize()
        self._created_indicators.append(indicator)
        return indicator

    def standard_deviation(self, source, periods):
        from Indicators.StandardDeviation import StandardDeviation
        indicator = StandardDeviation(source, periods)
        indicator.initialize()
        self._created_indicators.append(indicator)
        return indicator

    def bollinger_bands(self, source, periods, standard_deviations, ma_type):
        from Indicators.BollingerBands import BollingerBands
        indicator = BollingerBands(source, periods, standard_deviations, ma_type)
        indicator.initialize()
        self._created_indicators.append(indicator)
        return "", indicator

    def relative_strength_index(self, source, periods):
        from Indicators.RelativeStrengthIndex import RelativeStrengthIndex
        indicator = RelativeStrengthIndex(source, periods)
        indicator.initialize()
        self._created_indicators.append(indicator)
        return indicator

    def macd(self, source, fast_periods, slow_periods, signal_periods):
        from Indicators.MovingAverageConvergenceDivergence import MovingAverageConvergenceDivergence
        indicator = MovingAverageConvergenceDivergence(source, fast_periods, slow_periods, signal_periods)
        indicator.initialize()
        self._created_indicators.append(indicator)
        return indicator
