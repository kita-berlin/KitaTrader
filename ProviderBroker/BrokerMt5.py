import MetaTrader5 as mt5
from BrokerProvider import BrokerProvider
from AlgoApi import Symbol, Account

class BrokerMt5(BrokerProvider):
    def __init__(self, account: Account, parameter: str):
        super().__init__(account, parameter)
        pass

    def init(self, symbol: Symbol):
        para_split = self.parameter.split(",")
        is_mt5: bool = mt5.initialize(int(para_split[0]), para_split[1], para_split[2])

        if not is_mt5:
            print(
                "MT5 initialize() failed, error code =",
                mt5.last_error(),
            )
            quit()

        # add MT5 specific symbol appendix
        self.broker_symbol_name = mt5.symbols_get(symbol.name + "*")[0]
