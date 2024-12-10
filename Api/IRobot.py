from abc import ABC, abstractmethod
from KitaApi import Symbol


############### Interface needed for robots ####################
# The complete api which can be used by robots must be declarated here
# Varibales must be declared with their types
# Methods must be declared with their prototypes
class IRobot(ABC):

    # Methods to be overridden in the robot
    # region
    @abstractmethod
    def on_start(self) -> None: ...

    @abstractmethod
    def on_tick(self, symbol: Symbol): ...

    @abstractmethod
    def on_stop(self) -> None: ...

    @abstractmethod
    def get_tick_fitness(self) -> float: ...

    # endregion


# end of file
