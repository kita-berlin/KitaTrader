import os
import sys
import gzip
import struct
import pytz
import hashlib
import time
from datetime import datetime, timedelta
from lzma import LZMADecompressor, FORMAT_AUTO  # type: ignore
from Api.KitaApi import KitaApi, Symbol
from Api.Bars import Bars
from Api.KitaApiEnums import BidAsk
from Api.QuoteProvider import QuoteProvider
from Api.KitaApiEnums import *
from twisted.internet import reactor, ssl, protocol, task
from twisted.internet.defer import Deferred, inlineCallbacks, ensureDeferred
from ctrader_open_api import Client, Protobuf, TcpProtocol, Auth

# Add PyDownload messages directory to path for protobuf imports
_pydownload_messages_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                        'cTraderTools', 'Apps', 'PyDownload', 'messages')
if os.path.exists(_pydownload_messages_dir) and _pydownload_messages_dir not in sys.path:
    sys.path.insert(0, _pydownload_messages_dir)

from OpenApiCommonModelMessages_pb2 import ProtoPayloadType as ProtoCommonPayloadType
from OpenApiCommonMessages_pb2 import ProtoErrorRes
from OpenApiMessages_pb2 import (
    ProtoOAApplicationAuthReq, ProtoOAApplicationAuthRes,
    ProtoOAAccountAuthReq, ProtoOAAccountAuthRes,
    ProtoOAGetTickDataReq, ProtoOAGetTickDataRes,
    ProtoOASymbolsListReq, ProtoOASymbolsListRes,
    ProtoOARefreshTokenReq, ProtoOARefreshTokenRes,
)
from OpenApiModelMessages_pb2 import ProtoOAPayloadType, ProtoOAQuoteType


class QuoteCtraderCache(QuoteProvider):
    provider_name = "cTraderCache"
    _assets_file_name: str = "Assets_Pepperstone_Live.csv"
    _last_hour_base_timestamp: float = 0
    _prev_bid: float = 0
    _prev_ask: float = 0

    def __init__(self, data_rate: int, parameter: str = "", credentials: str = ""):
        assets_path = os.path.join("Files", self._assets_file_name)
        QuoteProvider.__init__(self, parameter, assets_path, data_rate)
        self.credentials_path = credentials

    def init_symbol(self, api: KitaApi, symbol: Symbol):
        self.api = api
        self.symbol = symbol
        ctrader_path = api.resolve_env_variables(self.parameter)
        self.cache_path = os.path.join(ctrader_path, self.symbol.name, "t1")
        
        # Check and download missing data if credentials are provided
        if self.credentials_path and os.path.exists(self.credentials_path):
            # Resolve dates manually as AllDataStartUtc is not set yet
            start_date = getattr(api, 'WarmupStart', datetime.min)
            if start_date == datetime.min:
                 # Fallback to BacktestStart
                 start_date = getattr(api, 'BacktestStart', datetime.min)
            
            end_date = getattr(api, 'BacktestEnd', datetime.max)
            
            # Ensure dates are UTC for consistent checks (Cache is UTC)
            if start_date != datetime.min:
                 # Strip timezone if present or ensure it handles comparisons correctly
                 # ensure_data_range logic handles comparisons with cache
                 self.ensure_data_range(start_date, end_date)
            
    def ensure_data_range(self, start_utc: datetime, end_utc: datetime):
        """Check if data exists for the full range. If days are missing, download them."""
        missing_days = []
        current = start_utc.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = end_utc.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Identify missing days
        while current < end_date:
            path = os.path.join(self.cache_path, current.strftime("%Y%m%d") + ".zticks")
            if not os.path.exists(path):
                self.api._debug_log(f"Missing data file: {path}")
                missing_days.append(current)
            current += timedelta(days=1)
            
        if not missing_days:
            return

        self.api._debug_log(f"Missing data for {len(missing_days)} days. Initiating download...")
        
        # Load credentials
        env = self._load_env(self.credentials_path)
        env['_credentials_path'] = self.credentials_path  # Store path for oauth_login import
        
        # Determine ranges
        missing_ranges = self._group_consecutive_days(missing_days)
        
        # Define internal downloader function for task.react
        def _run_internal_downloader(reactor):
             downloader = self.InternalDataDownloader(
                 env=env,
                 symbol_name=self.symbol.name,
                 symbol_id=0, # Will be resolved
                 target_dir=self.cache_path,
                 missing_ranges=missing_ranges,
                 logger=self.api._debug_log
             )
             return ensureDeferred(downloader.run())

        try:
             self.api._debug_log("Starting Twisted reactor for internal download...")
             task.react(_run_internal_downloader)
             self.api._debug_log("Internal download completed.")
        except Exception as e:
            self.api._debug_log(f"Download process finished with: {e}")

    def _group_consecutive_days(self, days):
        """Group consecutive timestamps into (start, end) tuples."""
        if not days: return []
        days.sort()
        ranges = []
        start = days[0]
        prev = days[0]
        for day in days[1:]:
             if day - prev > timedelta(days=1):
                 ranges.append((start, prev + timedelta(days=1)))
                 start = day
             prev = day
        ranges.append((start, prev + timedelta(days=1)))
        return ranges

    def _load_env(self, path):
        # Load env.txt keys
        config = {}
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    k, v = line.strip().split('=', 1)
                    config[k.strip()] = v.strip().strip('"\'')
        
        # Fallback/Default for App Creds if not in env.txt (usually strictly in quantrosoft_config)
        app_id = 'YOUR_APP_ID'
        app_secret = 'YOUR_SECRET'
        try:
             env_dir = os.path.dirname(os.path.abspath(path))
             if env_dir not in sys.path:
                 sys.path.insert(0, env_dir)
             import quantrosoft_config
             app_id = quantrosoft_config.QUANTROSOFT_CTRADER_APP_ID
             app_secret = quantrosoft_config.QUANTROSOFT_CTRADER_APP_SECRET
        except Exception as e:
             self.api._debug_log(f"Failed to load quantrosoft_config: {e}")

        return {
            'username': config.get('CTRADER_USERNAME', ''),
            'password': config.get('CTRADER_PASSWORD', ''),
            'account_id': config.get('CTRADER_ACCOUNT_ID', ''),
            'access_token': config.get('CTRADER_ACCESS_TOKEN', ''),
            'refresh_token': config.get('CTRADER_REFRESH_TOKEN', ''),
            'app_id': config.get('QUANTROSOFT_CTRADER_APP_ID', app_id),
            'app_secret': config.get('QUANTROSOFT_CTRADER_APP_SECRET', app_secret),
        }

    class InternalDataDownloader:
         def __init__(self, env, symbol_name, symbol_id, target_dir, missing_ranges, logger):
             self.env = env
             self.symbol = symbol_name
             self.symbol_id = symbol_id
             self.target_dir = target_dir
             self.ranges = missing_ranges
             self.log = logger
             self.client = None

         @inlineCallbacks
         def run(self):
             try:
                 # Monkey-patch TcpProtocol to use local Message definitions
                 # This fixes "Unexpected end-group tag" errors caused by library mismatch
                 from OpenApiCommonMessages_pb2 import ProtoMessage, ProtoHeartbeatEvent
                 import ctrader_open_api.tcpProtocol
                 import ctrader_open_api.protobuf
                 
                 self.client = Client("demo.ctraderapi.com", 5035, TcpProtocol)
                 
                 # Connection setup
                 connected_d = Deferred()
                 def on_connected(c):
                     if not connected_d.called:
                         connected_d.callback(c)
                 self.client.setConnectedCallback(on_connected)
                 
                 def on_disconnected(client, reason):
                     self.log(f"Disconnected: {reason}")
                 self.client.setDisconnectedCallback(on_disconnected)
                 
                 self.log("[InternalDownloader] Connecting...")
                 self.client.startService()
                 yield connected_d
                 self.log("[InternalDownloader] Connected.")
                 
                 # 1. App Auth
                 app_id = self.env.get('app_id')
                 from OpenApiMessages_pb2 import ProtoOAApplicationAuthReq
                 app_auth_req = ProtoOAApplicationAuthReq()
                 app_auth_req.clientId = app_id
                 app_auth_req.clientSecret = self.env.get('app_secret')
                 
                 self.log(f"[InternalDownloader] App Auth: {app_id[:5]}...")
                 res = yield self.client.send(app_auth_req, responseTimeoutInSeconds=30)
                 if res.payloadType == ProtoOAPayloadType.PROTO_OA_ERROR_RES:
                     err = ProtoErrorRes()
                     err.ParseFromString(res.payload)
                     self.log(f"App Auth Error: {err.errorCode} - {err.description}")
                     return
                 
                 # 2. Refresh Token
                 refresh_req = ProtoOARefreshTokenReq()
                 refresh_req.refreshToken = self.env.get('refresh_token')
                 res = yield self.client.send(refresh_req, responseTimeoutInSeconds=30)
                 
                 token_refreshed = False
                 if res.payloadType == ProtoOAPayloadType.PROTO_OA_REFRESH_TOKEN_RES:
                    refresh_res = ProtoOARefreshTokenRes()
                    refresh_res.ParseFromString(res.payload)
                    self.env['access_token'] = refresh_res.accessToken
                    self.env['refresh_token'] = refresh_res.refreshToken
                    self.log("[InternalDownloader] Token Refreshed.")
                    token_refreshed = True
                 elif res.payloadType == ProtoOAPayloadType.PROTO_OA_ERROR_RES:
                    err = ProtoErrorRes()
                    err.ParseFromString(res.payload)
                    self.log(f"Token Refresh Error: {err.errorCode} - {err.description}")
                    
                    # If token is invalid, try OAuth re-login
                    # Check both errorCode and description as the error may be in either field
                    error_text = f"{err.errorCode} {err.description}".upper()
                    if 'INVALID' in error_text or 'EXPIRED' in error_text or 'ACCESS_TOKEN' in error_text:
                        self.log("Refresh token expired, attempting OAuth re-login...")
                        try:
                            # Import oauth_login from PyDownload directory
                            import sys
                            pydownload_dir = os.path.dirname(os.path.abspath(self.env.get('_credentials_path', '')))
                            if pydownload_dir and pydownload_dir not in sys.path:
                                sys.path.insert(0, pydownload_dir)
                            
                            from oauth_login import perform_oauth_login
                            
                            # Perform OAuth login
                            tokens = perform_oauth_login(
                                app_id=self.env.get('app_id'),
                                app_secret=self.env.get('app_secret'),
                                username=self.env.get('username'),
                                password=self.env.get('password')
                            )
                            
                            self.env['access_token'] = tokens['access_token']
                            self.env['refresh_token'] = tokens['refresh_token']
                            self.log("OAuth re-login successful")
                            token_refreshed = True
                        except Exception as e:
                            self.log(f"OAuth re-login failed: {e}")
                            return
                 
                 if not token_refreshed:
                     self.log("Could not obtain valid access token")
                     return
                 
                 # 3. Resolve Account (Login ID -> Ctid ID)
                 from OpenApiMessages_pb2 import ProtoOAGetAccountListByAccessTokenReq, ProtoOAGetAccountListByAccessTokenRes
                 acc_list_req = ProtoOAGetAccountListByAccessTokenReq()
                 acc_list_req.accessToken = self.env.get('access_token')
                 res = yield self.client.send(acc_list_req)

                 resolved_acc_id = None
                 if res.payloadType == ProtoOAPayloadType.PROTO_OA_GET_ACCOUNTS_BY_ACCESS_TOKEN_RES:
                    acc_list_res = ProtoOAGetAccountListByAccessTokenRes()
                    acc_list_res.ParseFromString(res.payload)
                    config_acc_id = str(int(self.env.get('account_id'))) # Start with str comparison
                    
                    for acc in acc_list_res.ctidTraderAccount:
                        if str(acc.traderLogin) == config_acc_id:
                            resolved_acc_id = acc.ctidTraderAccountId
                            self.log(f"Resolved Account {config_acc_id} to ID {resolved_acc_id}")
                            break
                        if str(acc.ctidTraderAccountId) == config_acc_id:
                             resolved_acc_id = acc.ctidTraderAccountId
                             break
                 
                 if not resolved_acc_id:
                      if res.payloadType == ProtoOAPayloadType.PROTO_OA_ERROR_RES:
                           err = ProtoErrorRes()
                           err.ParseFromString(res.payload)
                           self.log(f"Account Resolver Error: {err.errorCode} - {err.description}")
                      else:
                           self.log("Account Resolver: Account not found in list")
                      return
                 
                 # Update env with resolved ID so other methods use it
                 self.env['account_id'] = str(resolved_acc_id)

                 # 4. Account Auth
                 acc_auth_req = ProtoOAAccountAuthReq()
                 acc_auth_req.ctidTraderAccountId = resolved_acc_id
                 acc_auth_req.accessToken = self.env.get('access_token')
                 res = yield self.client.send(acc_auth_req)
                 
                 if res.payloadType == ProtoOAPayloadType.PROTO_OA_ERROR_RES:
                     err = ProtoErrorRes()
                     err.ParseFromString(res.payload)
                     self.log(f"Account Auth Error: {err.errorCode} - {err.description}")
                     return
                 
                 self.log("[InternalDownloader] Account Authenticated.")
                 
                 # 5. Resolve Symbol
                 sym_req = ProtoOASymbolsListReq()
                 sym_req.ctidTraderAccountId = resolved_acc_id
                 res = yield self.client.send(sym_req)

                 if res.payloadType == ProtoOAPayloadType.PROTO_OA_ERROR_RES:
                     err = ProtoErrorRes()
                     err.ParseFromString(res.payload)
                     self.log(f"Error fetching symbols: {err.errorCode} - {err.description}")
                     return

                 sym_res = ProtoOASymbolsListRes()
                 sym_res.ParseFromString(res.payload)
                 
                 for s in sym_res.symbol:
                     if s.symbolName == self.symbol:
                         self.symbol_id = s.symbolId
                         break
                 
                 if not self.symbol_id:
                     self.log(f"Symbol {self.symbol} not found")
                     return

                 # 5. Download Ranges
                 if not os.path.exists(self.target_dir):
                     os.makedirs(self.target_dir)

                 for start_dt, end_dt in self.ranges:
                     self.log(f"[InternalDownloader] Downloading range {start_dt} to {end_dt}")
                     current = start_dt
                     while current < end_dt:
                         day_end = current + timedelta(days=1)
                         req_end = min(day_end, end_dt)
                         
                         yield self.download_day(current, req_end)
                         current += timedelta(days=1)

             except Exception as e:
                 self.log(f"[InternalDownloader] Error: {e}")
             finally:
                 if self.client:
                     try:
                         if hasattr(self.client, 'stopService'):
                             self.client.stopService()
                     except: pass

         @inlineCallbacks
         def download_day(self, start_dt, end_dt):
             try:
                 ticks = yield self.download_ticks(start_dt, end_dt)
                 filename = start_dt.strftime("%Y%m%d") + ".zticks"
                 path = os.path.join(self.target_dir, filename)
                 
                 # Always write, even if empty (creates cache entry)
                 self.write_ticks(path, ticks)
                 self.log(f"Saved {filename} ({len(ticks)} ticks)")
             except Exception as e:
                 self.log(f"Failed to download day {start_dt}: {e}")

         @inlineCallbacks
         def download_ticks(self, start_time, end_time):
             start_ms = int(start_time.timestamp() * 1000)
             end_ms = int(end_time.timestamp() * 1000) - 1 # Exclusive of next day start usually
             
             all_bid_ticks = []
             all_ask_ticks = []
             
             # Bids
             yield self._fetch_ticks(start_ms, end_ms, ProtoOAQuoteType.BID, all_bid_ticks)
             # Asks
             yield self._fetch_ticks(start_ms, end_ms, ProtoOAQuoteType.ASK, all_ask_ticks)
             
             all_bid_ticks.sort(key=lambda x: x[0])
             all_ask_ticks.sort(key=lambda x: x[0])
             return self.merge_ticks(all_bid_ticks, all_ask_ticks)

         @inlineCallbacks
         def _fetch_ticks(self, start_ms, end_ms, quote_type, result_list):
             current_to = end_ms
             while current_to > start_ms:
                 req = ProtoOAGetTickDataReq()
                 req.ctidTraderAccountId = int(self.env.get('account_id'))
                 req.symbolId = self.symbol_id
                 req.type = quote_type
                 req.fromTimestamp = start_ms
                 req.toTimestamp = int(current_to)
                 
                 res = yield self.client.send(req)
                 if res.payloadType != ProtoOAPayloadType.PROTO_OA_GET_TICKDATA_RES: break
                 
                 resp = ProtoOAGetTickDataRes()
                 resp.ParseFromString(res.payload)
                 ticks = resp.tickData
                 if not ticks: break
                 
                 decoded = self.decode_ticks(ticks, start_ms)
                 result_list.extend(decoded)
                 
                 min_ts = min(t[0] for t in decoded)
                 if min_ts <= start_ms: break
                 current_to = min_ts - 1
                 if len(ticks) < 1000 and not resp.hasMore and (current_to - start_ms < 1000): break

         def decode_ticks(self, raw_ticks, base_ms):
             decoded = []
             acc_ts = 0
             acc_price = 0
             year_2000_ms = 946684800000
             for t in raw_ticks:
                 if t.timestamp > 0 and t.timestamp > year_2000_ms:
                     acc_ts = 0
                     acc_price = 0
                 acc_ts += t.timestamp
                 acc_price += t.tick
                 abs_ts = acc_ts if acc_ts > year_2000_ms else base_ms + acc_ts
                 decoded.append((abs_ts, acc_price))
             return decoded

         def merge_ticks(self, bids, asks):
             quotes = []
             b_idx = a_idx = 0
             last_b = last_a = None
             while b_idx < len(bids) or a_idx < len(asks):
                 ts_b = bids[b_idx][0] if b_idx < len(bids) else float('inf')
                 ts_a = asks[a_idx][0] if a_idx < len(asks) else float('inf')
                 
                 if ts_b <= ts_a:
                     curr_ts = ts_b
                     last_b = bids[b_idx][1]
                     b_idx += 1
                 else:
                     curr_ts = ts_a
                     last_a = asks[a_idx][1]
                     a_idx += 1
                 
                 if last_b is not None and last_a is not None:
                     quotes.append((curr_ts, last_b, last_a))
             return quotes

         def write_ticks(self, path, quotes):
             with gzip.open(path, 'wb') as f:
                 for q in quotes:
                     f.write(struct.pack('<qqq', int(q[0]), int(q[1]), int(q[2])))


# ... (Rest of existing file)

    def get_day_at_utc(self, utc: datetime) -> tuple[str, datetime, Bars]:
        day_data: Bars = Bars(self.symbol.name, 0, 0)  # 0 = tick timeframe
        self.last_utc = run_utc = utc.replace(hour=0, minute=0, second=0, microsecond=0)

        path = os.path.join(self.cache_path, run_utc.strftime("%Y%m%d") + ".zticks")
        if os.path.exists(path):
            date_str = run_utc.strftime("%d.%m.%Y")
            # Loading message goes to debug log, not stdout/stderr
            if hasattr(self, 'api') and self.api:
                self.api._debug_log(f"Loading {date_str}")
            # Read the compressed file into a byte array
            with gzip.open(path, "rb") as decompressor:
                ba = decompressor.read()

            # Process the byte array to extract data
            # Match C# ReadCtDayV2 logic exactly
            source_ndx = 0
            target_ndx = 0  # Track index in day_data (like targetNdx in C#)
            # Use loaderTickSize = 10e-6 (0.00001) like C#
            loader_tick_size = 10e-6  # Same as C# const double loaderTickSize = 10e-6;
            
            # Store bid/ask as integers (like C# Tick2Bid/Tick2Ask arrays)
            tick_bids = []
            tick_asks = []
            tick_times = []
            
            while source_ndx < len(ba):
                # Read epoc milliseconds timestamp (8 bytes long) - same as C#
                timestamp_ms = struct.unpack_from("<q", ba, source_ndx)[0]
                source_ndx += 8
                
                append_datetime = datetime.fromtimestamp(timestamp_ms / 1000.0, tz=pytz.UTC)
                
                # Read bid as int (8 bytes, cast to int like C#: var bid = (int)BitConverter.ToInt64(...))
                bid_int = int(struct.unpack_from("<q", ba, source_ndx)[0])
                source_ndx += 8
                
                # Read ask as int (8 bytes, cast to int like C#: var ask = (int)BitConverter.ToInt64(...))
                ask_int = int(struct.unpack_from("<q", ba, source_ndx)[0])
                source_ndx += 8
                
                # Calculate TickVolume delta using cTrader's logic: 
                # if both Bid and Ask are updated (non-zero in zticks), volume delta is 2, else 1.
                # In cTrader source: return (!backtestingQuote.IsAskHit || !backtestingQuote.IsBidHit) ? 1 : 2;
                vol_delta = 2 if (bid_int > 0 and ask_int > 0) else 1
                
                # Match C# zero handling logic exactly (from ReadCtDayV2):
                # sa.Tick2Bid[targetNdx] = 0 == bid ? (0 == targetNdx ? ask : sa.Tick2Bid[targetNdx - 1]) : bid;
                # sa.Tick2Ask[targetNdx] = 0 == ask ? (0 == targetNdx ? bid : sa.Tick2Ask[targetNdx - 1]) : ask;
                # Note: C# evaluates bid first, then ask, so ask can use the updated bid value
                actual_bid_int = bid_int
                actual_ask_int = ask_int
                
                if actual_bid_int == 0:
                    if target_ndx == 0:
                        actual_bid_int = actual_ask_int  # First tick: use ask if bid is 0
                    else:
                        actual_bid_int = tick_bids[target_ndx - 1]  # Use previous bid from array
                
                if actual_ask_int == 0:
                    if target_ndx == 0:
                        actual_ask_int = actual_bid_int  # First tick: use bid if ask is 0
                    else:
                        actual_ask_int = tick_asks[target_ndx - 1]  # Use previous ask from array
                
                # Store resolved integers
                tick_bids.append(actual_bid_int)
                tick_asks.append(actual_ask_int)
                # Store volume delta in bids list temporarily, we will use it in append loop below
                tick_times.append((append_datetime, vol_delta))
                
                # Duplicate Filtering - REMOVED to match C# TickVolume
                # C# MarketData.GetBars() counts every tick line for volume even if prices are identical
                # Filtering for OnTick is handled in symbol_on_tick instead
                # if target_ndx > 0 and bid_int == tick_bids[-1] and ask_int == tick_asks[-1]:
                #     continue

                # Store as integers (like C# Tick2Bid/Tick2Ask arrays)
                # tick_bids.append(bid_int)
                # tick_asks.append(ask_int)
                # tick_times.append(append_datetime)
                target_ndx += 1
            
            # Now convert integers to doubles using loaderTickSize (like C# dPrice function)
            # dPrice(int iPrice, double tickSize) = tickSize * iPrice
            # Store both integers (for filtering) and floats (for API)
            for i in range(len(tick_times)):
                dt, v_delta = tick_times[i]
                append_bid = tick_bids[i] * loader_tick_size
                append_ask = tick_asks[i] * loader_tick_size
                
                day_data.append(
                    dt,
                    append_bid,
                    0, 0, 0,
                    float(v_delta),  # Store TickVolume delta in volume_bid field
                    append_ask,
                    0, 0, 0,
                    float(v_delta),  # Store TickVolume delta in volume_ask field
                )
        else:
            return "No data", self.last_utc, day_data

        return "", self.last_utc, day_data

    def get_first_datetime(self) -> tuple[str, datetime]:
        # List all files in the given path with the specific extension
        files = [file for file in os.listdir(self.cache_path) if file.endswith(".zticks")]

        # Sort the files in ascending order
        files.sort()
        if len(files) == 0:
            return "No files found at " + self.cache_path, datetime.min.replace(tzinfo=pytz.UTC)

        return "", datetime.strptime(files[0].split(".")[0], "%Y%m%d").replace(tzinfo=pytz.UTC)

    def get_highest_data_rate(self) -> int:
        return 0  # we can do ticks

    def _get_prevs_(self, utc: datetime, bid_ask: BidAsk, not_0: int) -> float:
        while True:
            utc -= timedelta(days=1)

            path = os.path.join(self.cache_path, utc.strftime("%Y%m%d") + ".zticks")
            assert os.path.exists(path), path + " does not exist"
            # Read the compressed file into a byte array
            with gzip.open(path, "rb") as decompressor:
                ba = decompressor.read()

            # Get the last value of the previous day
            if BidAsk.Bid == bid_ask:
                index = -16
            else:
                index = -8

            source_ndx = len(ba) + index
            while True:
                ret_val = struct.unpack_from("<q", ba, source_ndx)[0] * self.symbol.point_size
                if 0 != ret_val:
                    return ret_val
                source_ndx -= 24
                if source_ndx < 0:
                    assert False, "No non zero " + str(bid_ask)


# end of file
