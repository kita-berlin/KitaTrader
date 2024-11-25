import os
import math
import string
import csv
import math
import traceback
from typing import List
from datetime import datetime
from datetime import timedelta
from LeverageTier import LeverageTier
from MarketHours import MarketHours
from Asset import Asset
from Account import Account
from Bars import Bars
from Settings import BinSettings
from CoFu import *
from AlgoApiEnums import *


class MarketValues:
    def __init__(self):
        self.swap_long = 0.0
        self.swap_short = 0.0
        self.point_size = 0.0
        self.avg_spread = 0.0
        self.digits = 0
        self.point_value = 0.0
        self.margin_required = 0.0
        self.symbol_tz_id = ""
        self.market_open_time = timedelta()
        self.market_close_time = timedelta()
        self.min_lot = 0.0
        self.max_lot = 0.0
        self.commission = 0.0
        self.broker_symbol = ""
        self.symbol_leverage = 0.0
        self.lot_size = 0.0
        self.symbol_currency_base = ""
        self.symbol_currency_quote = ""


class ConcreteAsset(Asset):
    def __init__(self, name, digits):
        self._name = name
        self._digits = digits

    @property
    def name(self):
        return self._name

    @property
    def digits(self):
        return self._digits

    def convert(self, to, value):
        # Implement conversion logic here
        pass


class SymbolInfo:
    def __init__(self, trading_class, symbolName: str):
        self.trading_class = trading_class
        self.name = symbolName
        self.bars_list: list[Bars] = []

        # Platform specific inits
        if (
            Platform.mt5_live == self.trading_class.bin_settings.Platform
            or Platform.mt5_backtest == self.trading_class.bin_settings.Platform
        ):
            import MetaTrader5 as mt5

            is_mt5 = mt5.initialize(  # pylint: disable=no-member
                login=62060378, server="pepperstone_uk-Demo", password="tFue0y*akr"
            )

            if not is_mt5:
                print(
                    "MT5 initialize() failed, error code =",
                    mt5.last_error(),  # pylint: disable=no-member
                )
                quit()

            self.broker_symbol_name = mt5.symbols_get(  # pylint: disable=no-member
                self.name + "*"
            )[
                0
            ].name  # add MT5 specific symbol appendix

            from ..QuoteProviders.QuoteProviderMt5 import QuoteProvider
        pass

        if Platform.me_files == self.trading_class.bin_settings.Platform:
            try:
                from ..QuoteProviders.QuoteProviderMeFiles import QuoteProvider
            except:
                from QuoteProviders.QuoteProviderMeFiles import QuoteProvider

        if Platform.csv == self.trading_class.bin_settings.Platform:
            try:
                from ..QuoteProviders.QuoteProviderCsv import QuoteProvider
            except:
                from QuoteProviders.QuoteProviderCsv import QuoteProvider

        if Platform.mt5_live == self.trading_class.bin_settings.Platform:
            mt5.symbol_select(symbolName, True)  # pylint: disable=no-member
            symbol_info = mt5.symbol_info(symbolName)  # pylint: disable=no-member

            self.tick_size = symbol_info.trade_tick_size
            self.volume_in_units_min = (
                symbol_info.volume_min * symbol_info.trade_contract_size
            )
            self.volume_in_units_max = (
                symbol_info.volume_max * symbol_info.trade_contract_size
            )
            self.volume_in_units_step = (
                symbol_info.volume_step * symbol_info.trade_contract_size
            )
            self.leverage = self.trading_class.Account.leverage
            self.lot_size = symbol_info.trade_contract_size
            self.tick_value = symbol_info.trade_tick_value
            self.swap_long = symbol_info.swap_long
            self.swap_short = symbol_info.swap_short
            self.swap3_days_rollover = symbol_info.swap_rollover3days
            self.base_asset = symbol_info.currency_base
            self.quote_asset = symbol_info.currency_profit

            # On Mt5 commissions are in deal info
            self.commission = 0
            """
            # ENUM_SYMBOL_TRADE_MODE
            # SYMBOL_TRADE_MODE_DISABLED trade is disabled for the symbol
            # SYMBOL_TRADE_MODE_LONGONLY Allowed only long positions
            # SYMBOL_TRADE_MODE_SHORTONLY Allowed only short positions
            # SYMBOL_TRADE_MODE_CLOSEONLY Allowed only Position close operations
            # SYMBOL_TRADE_MODE_FULL No trade restrictions
            """
            self.is_trading_enabled = 4 == symbol_info.trade_mode

            self.trading_mode = SymbolTradingMode.fully_disabled
            if 4 == symbol_info.trade_mode:
                self.trading_mode = SymbolTradingMode.full_access
            if 3 == symbol_info.trade_mode:
                self.trading_mode = SymbolTradingMode.close_only
            """
            # swap_mode =1
            # ENUM_SYMBOL_SWAP_MODE:
            # SYMBOL_SWAP_MODE_DISABLED Swaps disabled (no swaps)
            # SYMBOL_SWAP_MODE_POINTS Swaps are charged in points
            # SYMBOL_SWAP_MODE_CURRENCY_SYMBOL Swaps are charged in money in base currency of the symbol
            # SYMBOL_SWAP_MODE_CURRENCY_MARGIN Swaps are charged in money in margin currency of the symbol
            # SYMBOL_SWAP_MODE_CURRENCY_DEPOSIT Swaps are charged in money, in client deposit currency
            # SYMBOL_SWAP_MODE_INTEREST_CURRENT Swaps are charged as the specified annual interest from the instrument price at calculation of swap (standard bank year is 360 days)
            # SYMBOL_SWAP_MODE_INTEREST_OPEN Swaps are charged as the specified annual interest from the open price of Position (standard bank year is 360 days)
            # SYMBOL_SWAP_MODE_REOPEN_CURRENT Swaps are charged by reopening positions. At the end of a trading day the Position is closed. Next day it is reopened by the close price +/- specified number of points (settings SYMBOL_SWAP_LONG and SYMBOL_SWAP_SHORT)
            # SYMBOL_SWAP_MODE_REOPEN_BID Swaps are charged by reopening positions. At the end of a trading day the Position is closed. Next day it is reopened by the current bid price +/- specified number of points (settings SYMBOL_SWAP_LONG and SYMBOL_SWAP_SHORT)
            """
            self.swap_calculation_type = SymbolSwapCalculationType.percentage
            if 1 == symbol_info.swap_mode:
                self.swap_calculation_type = SymbolSwapCalculationType.pips
            """
            # custom =False
            # chart_mode =0
            # select =True
            # visible =True
            # session_deals =0
            # session_buy_orders =0
            # session_sell_orders =0
            # volume =0
            # volumehigh =0
            # volumelow =0
            # time =1585069682
            # digits =3
            # spread =17
            # spread_float =True
            # ticks_bookdepth =10
            # trade_calc_mode =0
            # trade_mode =4
            # start_time =0
            # expiration_time =0
            # trade_stops_level =0
            # trade_freeze_level =0
            # trade_exemode =1
            # swap_mode =1
            # swap_rollover3days =3
            # margin_hedged_use_leg =False
            # expiration_mode =7
            # filling_mode =1
            # order_mode =127
            # order_gtc_mode =0
            # option_mode =0
            # option_right =0
            # bid =120.024
            # bidhigh =120.506
            # bidlow =118.798
            # ask =120.041
            # askhigh =120.526
            # asklow =118.828
            # last =0.0
            # lasthigh =0.0
            # lastlow =0.0
            # volume_real =0.0
            # volumehigh_real =0.0
            # volumelow_real =0.0
            # option_strike =0.0
            # point =0.001
            # trade_tick_value =0.8977708350166538
            # trade_tick_value_profit =0.8977708350166538
            # trade_tick_value_loss =0.8978272580355541
            # trade_tick_size =0.001
            # trade_contract_size =100000.0
            # trade_accrued_interest =0.0
            # trade_face_value =0.0
            # trade_liquidity_rate =0.0
            # volume_min =0.01
            # volume_max =500.0
            # volume_step =0.01
            # volume_limit =0.0
            # swap_long =-0.2
            # swap_short =-1.2
            # margin_initial =0.0
            # margin_maintenance =0.0
            # session_volume =0.0
            # session_turnover =0.0
            # session_interest =0.0
            # session_buy_orders_volume =0.0
            # session_sell_orders_volume =0.0
            # session_open =0.0
            # session_close =0.0
            # session_aw =0.0
            # session_price_settlement =0.0
            # session_price_limit_min =0.0
            # session_price_limit_max =0.0
            # margin_hedged =100000.0
            # price_change =0.0
            # price_volatility =0.0
            # price_theoretical =0.0
            # price_greeks_delta =0.0
            # price_greeks_theta =0.0
            # price_greeks_gamma =0.0
            # price_greeks_vega =0.0
            # price_greeks_rho =0.0
            # price_greeks_omega =0.0
            # price_sensitivity =0.0
            # basis =
            # category =
            # currency_base =EUR
            # currency_profit =JPY
            # currency_margin =EUR
            # bank =
            # description =Euro vs Japanese Yen
            # exchange =
            # formula =
            # isin =
            # name =EURJPY
            # page =http://www.google.com/finance?q =EURJPY
            # path =Forex\EURJPY
            """
        pass

        if (
            self.trading_class.bin_settings.Platform == Platform.me_files
            or self.trading_class.bin_settings.Platform == Platform.csv
            or self.trading_class.bin_settings.Platform == Platform.mt5_backtest
        ):
            broker = self.trading_class.Account.broker_symbol_name + (
                "_Live" if self.trading_class.Account.is_live else "_Demo"
            )
            # assets_dir = os.path.join(os.getenv("APPDATA"), "_Assets")
            assets_path = os.path.join("Files", f"Assets_{broker}.csv")
            self.trading_class.market_values = MarketValues()
            error = self.init_market_info(
                assets_path, symbolName, self.trading_class.market_values
            )
            if "" != error:
                print(error)
                exit()

            self.tick_size = self.trading_class.market_values.point_size
            self.volume_in_units_min = self.trading_class.market_values.min_lot
            self.volume_in_units_max = self.trading_class.market_values.max_lot
            self.volume_in_units_step = self.volume_in_units_min
            self.leverage = self.trading_class.market_values.symbol_leverage
            self.lot_size = self.trading_class.market_values.lot_size
            self.tick_value = self.trading_class.market_values.point_value
            self.commission = self.trading_class.market_values.commission
            self.swap_long = self.trading_class.market_values.swap_long
            self.swap_short = self.trading_class.market_values.swap_short
            self.swap3_days_rollover = 3
            self.base_asset = self.trading_class.market_values.symbol_currency_base
            self.quote_asset = self.trading_class.market_values.symbol_currency_quote
            self.swap_calculation_type: SymbolSwapCalculationType = (
                SymbolSwapCalculationType.pips
            )
            self.is_trading_enabled = True
            self.trading_mode = SymbolTradingMode.full_access

            self.quote_provider = (
                QuoteProvider(  # pylint: disable=possibly-used-before-assignment
                    self.trading_class, self
                )
            )
            error, quote = self.quote_provider.get_quote_at_date(
                self.trading_class.bin_settings.start_dt
            )
            if None == quote:
                print(error)
                quit()  # if there is an error getting 1st quote ==> fatal exit
            self.update_bars(quote)
            pass

    @property
    def tick_size(self):
        return self.__tick_size

    @tick_size.setter
    def tick_size(self, value):
        self.__tick_size = value
        self.digits = int(0.5 + math.log10(1 / value))

    @property
    def pip_value(self) -> float:
        return self.tick_value * 10

    @property
    def pip_size(self) -> float:
        return self.tick_size * 10

    dynamic_leverage: List[LeverageTier] = []

    @property
    def MarketHours(self) -> MarketHours:
        return MarketHours()

    def init_market_info(
        self, assets_path, symbol_name, market_values: MarketValues
    ) -> str:
        error = ""
        try:
            with open(assets_path, newline="") as csvfile:
                reader = csv.reader(csvfile)
                for line in reader:
                    if not line:
                        continue
                    line = [item.strip() for item in line]

                    if line[0] == "Name" and line[1] == "Price":
                        continue

                    if symbol_name != line[0]:
                        continue

                    if len(line) != 16:
                        return f"{assets_path} has wrong format (not 16 columns)"

                    market_values.swap_long = float(line[3])
                    market_values.swap_short = float(line[4])
                    market_values.point_size = float(line[5]) / 10.0
                    market_values.avg_spread = float(line[2]) / market_values.point_size
                    market_values.digits = int(
                        0.5 + math.log10(1 / market_values.point_size)
                    )
                    market_values.point_value = float(line[6]) / 10.0
                    market_values.margin_required = float(line[7])

                    market_time_split = line[8].split("-")
                    market_tzid_split = line[8].split(":")
                    market_values.symbol_tz_id = market_tzid_split[0].strip()
                    market_values.market_open_time = timedelta(
                        hours=int(market_tzid_split[1]),
                        minutes=int(market_tzid_split[2].split("-")[0]),
                    )
                    market_values.market_close_time = timedelta(
                        hours=int(market_time_split[1].split(":")[0]),
                        minutes=int(market_time_split[1].split(":")[1]),
                    )

                    market_values.min_lot = float(line[9])
                    market_values.max_lot = 10000 * market_values.min_lot
                    market_values.commission = float(line[10])
                    market_values.broker_symbol = line[11]
                    market_values.symbol_leverage = float(line[12])
                    market_values.lot_size = float(line[13])
                    market_values.symbol_currency_base = line[14].strip()
                    market_values.symbol_currency_quote = line[15].strip()
                    break
        except Exception as ex:
            error = str(ex)
            error += "\n" + traceback.format_exc()

        return error

    def update_bars(self, quote):
        for bars in self.bars_list:
            bars.update_bar(quote)

        self.time = quote.time
        self.bid = quote.open
        self.ask = quote.open_ask

    def on_tick(self) -> str:
        error, quote = self.quote_provider.get_next_quote()
        if None == quote:
            return error
        self.update_bars(quote)
        return ""


# end of file