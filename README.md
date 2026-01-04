# KitaTrader Comprehensive Architecture Overview

KitaTrader is a high-fidelity Python backtesting framework designed for professional algorithmic trading. This document details the architecture, data flow, and core design principles of the system.

## 1. Core Component Hierarchy

The framework follows a hierarchical structure for data ownership and execution:

### 1.1 `KitaApi` (The Robot Engine)
*   **Role**: The central orchestrator and base class for all trading robots.
*   **Responsibilities**:
    *   Managing the main execution loop (`do_tick`, `do_init`, `do_start`).
    *   Holding the `Account`, `Positions`, and `History`.
    *   Providing access to `MarketData` and `Indicators` factories.
    *   Managing the transition from **Internal Warm-up** to **User Execution**.

### 1.2 `Symbol` (The Data Gateway)
*   **Role**: Represents a single tradable instrument (e.g., AUDNZD).
*   **Responsibilities**:
    *   Owning symbol-specific metadata (Digits, PipSize, Leverage).
    *   Interfacing with the `QuoteProvider` to stream ticks.
    *   Conducting high-level tick validation and time-zone normalization.
    *   Propagating ticks downward to all attached `Bars` objects.

### 1.3 `Bars` & `Bar` (The Aggregation Layer)
*   **Role**: Transforms raw tick streams into time-series data.
*   **Responsibilities**:
    *   `Bars`: A collection of time-bound OHLCV bars for a specific timeframe (M1, H1, etc.).
    *   `Bar`: A lightweight object representing a single point in history.
    *   **Incremental Building**: Bars are built tick-by-tick. When a tick exceeds the current timeframe boundary, the current bar is "closed" (frozen) and a new one is initialized.

### 1.4 `DataSeries` & `TimeSeries` (The Storage Layer)
*   **Role**: Memory-efficient storage for price and indicator data.
*   **Responsibilities**:
    *   **Ringbuffer Backend**: Uses fixed-size circular buffers to prevent memory growth during long backtests.
    *   **Absolute Indexing**: Supports `series[i]` where `i` is the absolute 0-indexed count of values ever added, mapping it transparently to the circular buffer position.
    *   **Rounding**: Automatically rounds price data to `symbol.digits` to maintain parity with cTrader's fixed-precision engine.

---

## 2. The Tick Lifecycle

Every tick loaded from the source (e.g., `.zticks` cache) flows through the following pipeline:

1.  **Loading**: `QuoteCtraderCache` yields raw `(time, bid, ask, volume_delta)`.
2.  **Symbol Processing**: `Symbol.symbol_on_tick()` updates the symbol's current quote and spread.
3.  **Bar Aggregation**: `Bars.bars_on_tick()` updates the current OHLCV values.
4.  **Internal Chain**: The framework checks if it is in the "Warm-up" phase.
    *   *If Warm-up*: Indicators are updated (internally), but **NO user logic is called**.
    *   *If User Execution*: The framework calls `Robot.on_tick()`.
5.  **Bar Closure**: If the tick opens a new bar, `BarOpened` events fire (only after `BacktestStart`).

### 2.1 Warmup Period vs Backtest Start - Critical Architecture

**IMPORTANT**: The framework distinguishes between internal processing (warmup) and bot event handler execution:

#### Warmup Period (`WarmupStart` to `BacktestStart`)
- **Purpose**: Internal processing only - building bars, calculating indicators
- **What happens**:
  - ✅ Ticks are processed from `WarmupStart` onwards
  - ✅ Bars are built incrementally from ticks
  - ✅ Indicators are calculated (for warmup)
  - ❌ **NO bot event handlers are called** during warmup
  - ❌ `OnTick()` is **NOT** called
  - ❌ `OnBar()` is **NOT** called
  - ❌ `BarOpened` events do **NOT** fire

#### Backtest Start (`BacktestStart` onwards)
- **Purpose**: Bot logic execution - trading decisions, logging
- **What happens**:
  - ✅ Ticks are processed
  - ✅ Bars are built incrementally from ticks
  - ✅ Indicators are calculated
  - ✅ `OnTick()` is called when `symbol.time >= BacktestStartUtc`
  - ✅ `OnBar()` is called when `symbol.time >= BacktestStartUtc`
  - ✅ `BarOpened` events fire when `symbol.time >= BacktestStartUtc`

#### Implementation
- `Symbol.is_warm_up` flag is set in `symbol_on_tick()`: `self.is_warm_up = self.time < self.api.robot._BacktestStartUtc`
- `KitaApi.do_tick()` checks `is_warm_up` and skips calling `robot.on_tick()` during warmup
- `Bars._fire_bar_opened_event()` checks `is_warm_up` and only fires events after `BacktestStart`

This ensures that bot event handlers only receive data from `BacktestStart` onwards, matching cTrader CLI behavior where the backtest engine only processes data from the start date.

### 2.2 Date Range Filtering - Platform-Controlled

**CRITICAL ARCHITECTURE PRINCIPLE**: Date range filtering (start/end time behavior) is controlled **"under the hood"** by the platform/API layer, **NOT** by the bot code itself.

#### Platform Responsibility
- The platform (cTrader CLI/GUI or KitaTrader API) handles all date range filtering based on:
  - CLI parameters: `--start` and `--end` (for cTrader CLI)
  - Python API: `BacktestStart` and `BacktestEnd` properties (for KitaTrader)
- The platform ensures that:
  - Ticks outside the date range are never sent to the bot
  - Bars outside the date range are never created or passed to event handlers
  - Event handlers (`OnTick`, `OnBar`, `BarOpened`) only receive data within the specified range

#### Bot Code Responsibility
- **Bot code must NOT contain hardcoded date ranges**
- **Bot code must NOT filter by date/time in event handlers**
- Bot code should assume that any data it receives is already within the valid date range
- Bot code should log/process all bars/ticks that reach it, trusting the platform has already filtered appropriately

#### Implementation Details
- **Python (KitaTrader)**:
  - `KitaApi.do_init()` converts `BacktestStart` and `BacktestEnd` to UTC and stores as `_BacktestStartUtc` and `_BacktestEndUtc`
  - `KitaApi.do_tick()` stops processing when `symbol.time > _BacktestEndUtc`
  - `Bars._fire_bar_opened_event()` suppresses events when new bar open time (when previous bar closes) is `>= _BacktestEndUtc`
  - Bot event handlers (`on_tick`, `on_bar`, `BarOpened`) only receive data within `[BacktestStartUtc, BacktestEndUtc)`

- **C# (cTrader)**:
  - cTrader CLI/GUI handles date filtering based on `--start` and `--end` parameters
  - The cTrader platform ensures `OnTick`, `OnBar`, and `BarOpened` events only fire for data within the specified range
  - Bot code should not contain `mStartDate`/`mEndDate` fields or date filtering logic

#### Rationale
This separation of concerns ensures:
1. **Consistency**: Both Python and C# bots behave identically when given the same date range
2. **Simplicity**: Bot code focuses on trading logic, not date management
3. **Correctness**: Date range interpretation (inclusive vs exclusive) is handled consistently by the platform
4. **Maintainability**: Date range logic is centralized in one place (the platform), not scattered across bot code

---

## 3. Indicator System (Lazy & Recursive)

Indicators are designed with an optimized execution model:

*   **Lazy Execution**: Indicators only calculate their value for a specific index when that index is accessed (e.g., `sma.Result[index]`).
*   **Dependency Resolution**: If Indicator A (MACD) depends on Indicator B (EMA), requesting A will automatically verify and trigger a lazy update of B.
*   **Stateful Gap-Filling**: For recursive indicators (like EMA), if a request skip bars, the framework automatically calculates the missing indices in order to maintain mathematical continuity.
*   **Internal Warm-up**: The framework uses `WarmupStart` (explicitly set or calculated) to process ticks internally. It runs a "hidden" tick loop from `WarmupStart` to `BacktestStart` to fill the ring buffers and calculate indicators, but **NO bot event handlers are called** during this period. Bot event handlers (`OnTick`, `OnBar`, `BarOpened`) only fire after `BacktestStart` is reached.

### 3.1 Indicator Creation - Initialization Only

**CRITICAL ARCHITECTURE PRINCIPLE**: Indicator creation (e.g., `CreateSMAIndicators`, `BollingerBands`) must **ONLY** be done during initialization (`on_init()` in Python, `OnStart()` in C#), **NOT** in `on_start()` or `on_tick()`/`OnTick()`.

#### Rationale
- **Warmup Phase Guarantee**: The warmup phase processes ticks from `WarmupStart` to `BacktestStart`, ensuring that enough bars are available by the time the bot's event handlers are called.
- **Consistency**: Both Python and C# bots create indicators during initialization, ensuring identical behavior.
- **Simplicity**: Bot code doesn't need to check if enough bars are available - the warmup phase guarantees this.
- **Performance**: Creating indicators once during initialization is more efficient than checking and creating them repeatedly in event handlers.

#### Implementation
- **Python**: Indicators are created in `on_init()` method
- **C#**: Indicators are created in `OnStart()` method (which is the initialization phase in cTrader)
- **No Conditional Creation**: Indicators are created unconditionally during initialization - no need to check `bars.Count >= periods` since warmup ensures sufficient bars

---

## 4. Trading & Execution Simulation

The framework simulates broker interactions through a decoupled provider model:

*   **`TradeProvider`**: An abstract interface defining market entries and exits.
*   **`TradePaper`**: The standard backtesting provider.
    *   **Market Orders**: Executes trades at the current Bid/Ask.
    *   **Margin Tracking**: Calculates and reserves margin based on leverage.
    *   **PnL Calculation**: Updates the `Account.balance` upon position closure using point-value math.
*   **`Position`**: Tracks entry price, time, volume, label, and unrealized profit.
*   **`Account`**: Tracks Balance, Equity, Margin, and Free Margin.

---

## 5. Optimized Memory Management

KitaTrader is built for performance on commodity hardware:

*   **Fixed-Size Buffers**: All `DataSeries` and `Bars` use optimized `Ringbuffer` instances. This caps memory usage regardless of backtest length.
*   **Zero Horizontal Loading**: No data is pre-loaded into RAM at startup. The framework streams from disk and discards old data as the ring buffer head moves forward.
*   **Lazy Indicator Results**: Indicator result storage is also ring-buffered, typically sized to exactly match the indicator's period requirement.

---

## 6. Accuracy and Precision Principles

To ensure maximum accuracy and reliability:
1.  **Volume Logic**: `TickVolume` increments by 1 for single hit and 2 for simultaneous bid/ask changes, following industry-standard tick accumulation.
2.  **Indexing**: Absolute indexing supports both `[index]` and `.Last(n)` syntax for intuitive data access.
3.  **Indicator Math**: Each indicator implements precise mathematical formulas with proper seed handling and shift support.
4.  **Double Precision**: All calculations use full double precision (Python float) without premature rounding.

---

## 7. Integrated cTrader Data Download System

KitaTrader includes a fully autonomous data download system that automatically fetches missing historical tick data from cTrader's Open API when needed during backtesting.

### 7.1 Architecture Overview

The download system is implemented as an internal component of `QuoteCtraderCache`:

*   **`InternalDataDownloader`**: A nested class within `QuoteCtraderCache` that handles all API communication.
*   **Automatic Detection**: During `init_symbol()`, the system checks for missing `.zticks` files in the required date range.
*   **Synchronous Coordination**: Uses `twisted.internet.task.react` to run the asynchronous Twisted reactor in a blocking manner, ensuring downloads complete before backtesting begins.
*   **Standard Cache Structure**: Downloads data to the standard cTrader cache location: `{APPDATA}\Spotware\Cache\Spotware\BacktestingCache\V1\{account}\{symbol}\t1\`

### 7.2 Authentication Flow

The downloader implements a robust multi-stage authentication process:

1.  **Application Authentication**:
    *   Sends `ProtoOAApplicationAuthReq` with `APP_ID` and `APP_SECRET` from `quantrosoft_config.py`
    *   Establishes the application's identity with the cTrader API

2.  **Token Refresh with OAuth Fallback**:
    *   Attempts to refresh the access token using `ProtoOARefreshTokenReq` with the stored refresh token
    *   If refresh fails (token expired/invalid), automatically triggers OAuth re-authentication:
        *   Imports `oauth_login.perform_oauth_login` from the PyDownload directory
        *   Uses Playwright to perform headless browser authentication
        *   Obtains fresh access and refresh tokens
        *   Updates the environment dictionary with new tokens

3.  **Account Resolution**:
    *   Sends `ProtoOAGetAccountListByAccessTokenReq` to fetch all available accounts
    *   Matches the user's account ID (login number, e.g., 5166098) against `traderLogin` field
    *   Resolves to the internal `ctidTraderAccountId` (e.g., 45648662) required for API calls
    *   This mapping is critical because cTrader's API uses internal IDs, not visible account numbers

4.  **Account Authentication**:
    *   Sends `ProtoOAAccountAuthReq` with the resolved `ctidTraderAccountId`
    *   Establishes access to the specific trading account's data

5.  **Symbol Resolution**:
    *   Sends `ProtoOASymbolsListReq` to fetch all available symbols for the account
    *   Matches the symbol name (e.g., "AUDNZD") to get the `symbolId`

### 7.3 Data Download Process

Once authenticated, the downloader fetches tick data:

1.  **Range Processing**: Groups consecutive missing days into ranges to minimize API calls
2.  **Tick Retrieval**: For each day:
    *   Sends `ProtoOAGetTickDataReq` for both BID and ASK quotes separately
    *   Handles pagination (cTrader returns max ~1000 ticks per request)
    *   Decodes delta-encoded timestamps and prices
3.  **Tick Merging**: Combines BID and ASK streams into synchronized quote tuples
4.  **File Writing**: Saves to `.zticks` files in gzip-compressed format with the structure:
    *   Each tick: `struct.pack('<qqq', timestamp_ms, bid_int, ask_int)`
    *   Matches cTrader's exact binary format for seamless integration

### 7.4 Protobuf Message Integration

The system uses protobuf message definitions shared with the PyDownload tool:

*   **Shared Messages Directory**: `cTraderTools/Apps/PyDownload/messages/`
*   **Dynamic Path Resolution**: `QuoteCtraderCache.py` automatically adds this directory to `sys.path`
*   **Message Types Used**:
    *   `OpenApiCommonMessages_pb2`: `ProtoMessage`, `ProtoErrorRes`
    *   `OpenApiMessages_pb2`: Authentication, account, symbol, and tick data request/response messages
    *   `OpenApiModelMessages_pb2`: Enums for payload types and quote types
*   **No Local Duplication**: KitaTrader does not maintain its own copy of protobuf definitions

### 7.5 Error Handling and Resilience

The download system includes comprehensive error handling:

*   **Token Expiration**: Automatically detects and handles expired tokens via OAuth re-login
*   **API Errors**: Checks `payloadType` for `PROTO_OA_ERROR_RES` and logs detailed error information
*   **Connection Issues**: Gracefully handles disconnections and reports them to the debug log
*   **Missing Data**: Creates empty `.zticks` files for days with no trading activity (weekends, holidays)
*   **Validation**: Verifies each authentication step before proceeding to the next

### 7.6 Configuration and Credentials

The system requires minimal configuration:

*   **Credentials File**: Path to `env.txt` (typically in PyDownload directory) containing:
    *   `CTRADER_USERNAME`: cTrader ID username
    *   `CTRADER_PASSWORD`: cTrader ID password
    *   `CTRADER_ACCOUNT_ID`: Trading account number (visible in cTrader)
    *   `CTRADER_ACCESS_TOKEN`: OAuth access token (auto-updated)
    *   `CTRADER_REFRESH_TOKEN`: OAuth refresh token (auto-updated)
*   **App Credentials**: Loaded from `quantrosoft_config.py`:
    *   `QUANTROSOFT_CTRADER_APP_ID`
    *   `QUANTROSOFT_CTRADER_APP_SECRET`
*   **Data Path**: Uses standard cTrader cache location (C: drive), not the PyDownload cache path

### 7.7 Integration with Backtesting

The download system is seamlessly integrated into the backtesting workflow:

1.  **Initialization**: When `QuoteCtraderCache.init_symbol()` is called, it checks for missing data
2.  **Blocking Download**: If data is missing, the reactor runs and blocks until all downloads complete
3.  **Transparent to Robot**: The robot code never knows whether data was pre-cached or just downloaded
4.  **Performance**: Downloads ~100K-200K ticks per day in 10-15 seconds per day
5.  **Logging**: All download activity is logged to the robot's debug log for transparency

### 7.8 Design Principles

The integrated downloader follows these key principles:

*   **Zero External Dependencies**: No subprocess calls to external scripts
*   **Autonomous Operation**: Handles authentication, token refresh, and error recovery automatically
*   **Standard Compliance**: Uses cTrader's official cache structure and binary format
*   **Single Source of Truth**: Credentials only used for authentication, not path configuration
*   **Minimal Footprint**: Only imports Twisted and protobuf libraries when download is needed
*   **Fail-Safe**: If download fails, the backtest fails early with clear error messages rather than producing invalid results
