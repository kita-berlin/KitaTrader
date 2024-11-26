from abc import ABC, abstractmethod
from KitaSymbol import Symbol

###################################
class IRobot(ABC):
    symbol: Symbol

    ###################################
    @abstractmethod
    def on_start(self, is_long):
        pass

    ###################################
    @abstractmethod
    def on_tick(self):
        pass

    ###################################
    @abstractmethod
    def on_stop(self):
        pass

    ###################################
    # abstractmethod
    def get_tick_fitness(self):
        pass

# end of file
