from abc import ABC, abstractmethod


class IIndicator(ABC):
    _isLastBar: bool = False
    index: int = 0

    @property
    def is_last_bar(self) -> bool:
        """Returns true if Calculate is invoked for the last bar."""
        return self._isLastBar

    @is_last_bar.setter
    def is_last_bar(self, value: bool):
        self._is_last_bar = value

    @abstractmethod
    def calculate(self, index: int):
        """Calculate the value(s) of the indicator for the given index."""
        pass

    @abstractmethod
    def initialize(self):
        """Custom initialization for the Indicator. This method is invoked when an indicator is launched."""
        pass

    def on_destroy(self):
        """Called when Indicator is destroyed."""
        pass

    def __str__(self) -> str:
        """The name of the indicator derived class."""
        return self.__class__.__name__


# end of file
