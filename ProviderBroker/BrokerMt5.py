import MetaTrader5 as mt5
from BrokerProvider import BrokerProvider


class BrokerMt5(BrokerProvider):
    # login=62060378, server="pepperstone_uk-Demo", password="tFue0y*akr"
    def __init__(self, parameter: str):
        self.parameter = parameter
        pass

    def init(self, symbol_name: str):
        para_split = self.parameter.split(",")
        is_mt5: bool = mt5.initialize(int(para_split[0]), para_split[1], para_split[2])

        if not is_mt5:
            print(
                "MT5 initialize() failed, error code =",
                mt5.last_error(),
            )
            quit()

        # add MT5 specific symbol appendix
        self.broker_symbol_name = mt5.symbols_get(symbol_name + "*")[0]
