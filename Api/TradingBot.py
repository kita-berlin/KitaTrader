from abc import ABC, abstractmethod


###################################
class TradingBot(ABC):

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
