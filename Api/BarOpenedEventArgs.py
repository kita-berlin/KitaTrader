"""
BarOpenedEventArgs - Provides data for the event when a new bar opened on the chart.
Matches cTrader API: cAlgo.API.BarOpenedEventArgs
"""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Api.Bars import Bars


class BarOpenedEventArgs:
    """
    Provides data for the event when a new bar opened on the chart.
    
    Example:
        def on_start(self):
            self.Bars.BarOpened += self.Bars_BarOpened
        
        def Bars_BarOpened(self, args: BarOpenedEventArgs):
            new_bar = args.Bars.LastBar  # Or args.Bars.Last(0)
            closed_bar = args.Bars.Last(1)  # Previous closed bar
    """
    
    def __init__(self, bars: Bars):
        """
        Initialize BarOpenedEventArgs.
        
        Args:
            bars: The Bars object that triggered the event
        """
        self.Bars = bars
