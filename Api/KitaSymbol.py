from datetime import datetime
from SymbolInfo import SymbolInfo
from Settings import *
from AlgoApiEnums import *


######################################
class Symbol(SymbolInfo):
    def __init__(self, algo_api, symbolName: str):
        super().__init__(algo_api, symbolName)

    ######################################
    @property
    def spread(self):
        return self.Ask - self.Bid

    def normalize_volume_in_units(self, volume, rounding_mode=RoundingMode.ToNearest):
        mod = volume % self.volume_in_units_min
        floor = volume - mod
        ceiling = floor + self.volume_in_units_min
        if RoundingMode.Up == rounding_mode:
            return ceiling

        elif RoundingMode.Down == rounding_mode:
            return floor

        else:
            return floor if volume - floor < ceiling - volume else ceiling

    def quantity_to_volume_in_units(self, quantity):
        return quantity * self.lot_size
        pass

    def volume_in_units_to_quantity(self, volume):
        return volume / self.lot_size
        pass
