from datetime import datetime
from SymbolInfo import SymbolInfo
from Settings import *
from AlgoApiEnums import *


######################################
class Symbol(SymbolInfo):
    def __init__(self, tradingClass, symbolName: str):
        super().__init__(tradingClass, symbolName)

    ######################################
    @property
    def spread(self):
        return self.ask - self.bid

    def normalize_volume_in_units(self, volume, rounding_mode=RoundingMode.to_nearest):
        mod = volume % self.volume_in_units_min
        floor = volume - mod
        ceiling = floor + self.volume_in_units_min
        if rounding_mode.up == rounding_mode:
            return ceiling

        elif rounding_mode.down == rounding_mode:
            return floor

        else:
            return floor if volume - floor < ceiling - volume else ceiling

    def quantity_to_volume_in_units(self, quantity):
        return quantity * self.lot_size
        pass

    def volume_in_units_to_quantity(self, volume):
        return volume / self.lot_size
        pass
