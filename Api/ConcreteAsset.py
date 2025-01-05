from Api.Asset import Asset


class ConcreteAsset(Asset):
    def __init__(self, name: str, digits: int):
        self._name = name
        self._digits = digits

    @property
    def name(self) -> str:
        return self.name

    @property
    def digits(self) -> int:
        return self._digits

    # def convert(self, to: Asset, value: float) -> None:
    # Implement conversion logic here


# end of file
