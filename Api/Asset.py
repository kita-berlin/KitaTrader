from abc import ABC, abstractmethod


class Asset(ABC):
    """
    The Asset represents a currency.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        The Asset Name
        """
        return ""

    @property
    @abstractmethod
    def digits(self) -> int:
        """
        Number of Asset digits
        """
        return 0

    @abstractmethod
    def convert(self, to: float, value: float):
        """
        Converts value to another Asset.

        gui_parameters:
          to:
            Target Asset

          value:
            The value you want to convert from current Asset

        Returns:
            Value in to / target Asset
        """
        if isinstance(to, Asset):
            # Handle conversion to Asset
            return None

        elif isinstance(to, str):
            # Handle conversion to string
            return None

        else:
            raise ValueError("Unsupported conversion target")


# end of file
