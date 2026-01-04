"""
Indicators factory class - stub for testing
"""
class Indicators:
    def __init__(self, api=None, bot=None):
        self._api = api or bot
        self._created_indicators = []
    
    def simple_moving_average(self, source, periods):
        from Indicators.SimpleMovingAverage import SimpleMovingAverage
        
        # Check if an indicator with these parameters already exists
        # This is a basic check - in a full implementation we might want better caching
        # But for now, we just create a new one every time as per the C# behavior (which usually creates new instances)
        
        indicator = SimpleMovingAverage(source, periods)
        # indicator.initialize() # Not needed as __init__ handles setup and logic is in calculate()
        self._created_indicators.append(indicator)
        
        return indicator
