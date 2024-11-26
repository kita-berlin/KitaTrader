from datetime import timedelta
from Bars import Bars


class MarketDataClass:
    def __init__(self, algo_api):
        self.algo_api = algo_api
        pass

    def get_bars(self, timeframeSeconds, symbolName) -> Bars:
        new_bars = Bars(self.algo_api, timeframeSeconds, symbolName)
        symbol = self.algo_api.symbol_dictionary[symbolName]
        symbol.bars_list.append(new_bars)

        # build bars
        bars_start_dt = self.algo_api.bin_settings.start_dt - timedelta(
            seconds=1000 * timeframeSeconds
        )
        error, quote = symbol.quote_provider.get_quote_at_date(bars_start_dt)
        new_bars.update_bar(quote)

        while True:
            error, quote = symbol.quote_provider.get_next_quote()
            if "" != error:
                break

            new_bars.update_bar(quote)
            if (
                new_bars.open_times.count > 0
                and quote.time >= self.algo_api.bin_settings.start_dt
            ):
                break
        pass
        return new_bars


class MarketDataParent:
    def __init__(self):
        self.market_data = MarketDataClass(self)

    """
    def get_ticks(self, symbolName: str = None) -> 'ticks':
        if symbolName:
            # Implementation for getting tick data for a specific symbol
            pass
        else:
            # Implementation for getting tick data
            pass
    """
