# DataPath Configuration Guide

## 📍 **Where to Set DataPath for QuantConnect Data**

The `DataPath` needs to be set to the **base directory** - KitaTrader will automatically add subdirectories.

---

## ✅ **Correct Configuration:**

### **For `MainConsole.py`:**
```python
# Line 28-30
self.robot.DataPath = r"G:\Meine Ablage\ShareFile\RoadToSuccess - General\Historical Data - UTC\NinjaTrader\6B\QuantConnect Seconds"
```

### **For `MainUltron.py`:**
```python
# Line 47
self.robot.DataPath = r"G:\Meine Ablage\ShareFile\RoadToSuccess - General\Historical Data - UTC\NinjaTrader\6B\QuantConnect Seconds"
```

### **For Optimizers (`GeneticOptimizer.py`, `WalkForwardOptimizer.py`):**
```python
# Inside run_backtest() method
robot.DataPath = r"G:\Meine Ablage\ShareFile\RoadToSuccess - General\Historical Data - UTC\NinjaTrader\6B\QuantConnect Seconds"
```

---

## 📂 **How KitaTrader Builds the Full Path:**

### **Base Path (what you set):**
```
G:\Meine Ablage\ShareFile\RoadToSuccess - General\Historical Data - UTC\NinjaTrader\6B\QuantConnect Seconds
```

### **System adds subdirectories:**
```
{DataPath}/QuoteQuantConnect/minute/GBPUSD/
```

### **Final path used:**
```
G:\Meine Ablage\ShareFile\RoadToSuccess - General\Historical Data - UTC\NinjaTrader\6B\QuantConnect Seconds\QuoteQuantConnect\minute\GBPUSD\20240318_quote.zip
```

**Breakdown:**
- `{DataPath}` - Your base path
- `QuoteQuantConnect` - Provider name (auto-added)
- `minute` - Bar timeframe folder (auto-added)
- `GBPUSD` - Symbol name (auto-added)
- `20240318_quote.zip` - Data file

---

## 🔄 **Switching Between Data Sources:**

### **For QuantConnect:**
```python
# Set in optimizer_config.json
"data_source": "QuantConnect"
"symbol_name": "GBPUSD"

# Set in MainConsole.py / MainUltron.py
self.robot.DataPath = r"G:\Meine Ablage\ShareFile\RoadToSuccess - General\Historical Data - UTC\NinjaTrader\6B\QuantConnect Seconds"
```

### **For Dukascopy:**
```python
# Set in optimizer_config.json
"data_source": "Dukascopy"
"symbol_name": "EURUSD"

# Set in MainConsole.py / MainUltron.py
self.robot.DataPath = "$(OneDrive)/KitaData/cfd"
```

---

## 📊 **Data Structure Required:**

Your QuantConnect data must be organized as:

```
G:\...\QuantConnect Seconds\
  └── QuoteQuantConnect\
      └── minute\
          └── GBPUSD\
              ├── 20240314_quote.zip
              ├── 20240315_quote.zip
              ├── 20240318_quote.zip
              └── ... (491 files)
```

**Note:** The organization script already created this structure when you ran `MainUltron.py`!

---

## 🎯 **Quick Test:**

After setting the DataPath, test with:

```bash
# Using MainConsole.py
python MainConsole.py

# Using MainUltron.py
python MainUltron.py
```

Both should now load your QuantConnect data correctly!

---

## 🔍 **Verify Data Path:**

Check if the path exists:
```bash
dir "G:\Meine Ablage\ShareFile\RoadToSuccess - General\Historical Data - UTC\NinjaTrader\6B\QuantConnect Seconds\QuoteQuantConnect\minute\GBPUSD"
```

Should show 491 zip files.

---

## ⚠️ **Common Mistakes:**

### ❌ **WRONG - Including subdirectories:**
```python
self.robot.DataPath = r"G:\...\QuantConnect Seconds\QuoteQuantConnect\minute\GBPUSD"
```

### ✅ **CORRECT - Base path only:**
```python
self.robot.DataPath = r"G:\...\QuantConnect Seconds"
```

KitaTrader automatically adds: `\QuoteQuantConnect\minute\GBPUSD\`

---

## 📝 **Summary:**

**Set `DataPath` to:**
```python
r"G:\Meine Ablage\ShareFile\RoadToSuccess - General\Historical Data - UTC\NinjaTrader\6B\QuantConnect Seconds"
```

**In these files:**
- ✅ `MainConsole.py` (line 29) - Updated
- ✅ `MainUltron.py` (line 47) - Updated
- ✅ `Optimizers/GeneticOptimizer.py` (line 108) - Needs update
- ✅ `Optimizers/WalkForwardOptimizer.py` (line 149) - Needs update
- ✅ `Environments/UltronEnv.py` (line 103) - Needs update

---

## 🚀 **You're Ready!**

Run your backtest now:
```bash
python MainConsole.py
```

It will load QuantConnect data from your G: drive! 🎯

---

## 📦 **cTrader Cache Configuration**

### **For cTrader Historical Data:**

KitaTrader can automatically download and use cTrader's historical tick data from the standard Spotware cache.

#### **Configuration:**

```python
# In OHLCTestConsole.py or your robot script
self.robot.DataPath = r"C:\Users\{YourUsername}\AppData\Roaming\Spotware\Cache\Spotware\BacktestingCache\V1\demo_19011fd1"

# Quote Provider with automatic download
self.robot.quote_provider = QuoteCtraderCache(
    data_rate=0,  # Tick data
    parameter=self.robot.DataPath,
    credentials=r"C:\Users\{YourUsername}\Documents\Source\cTraderTools\Apps\PyDownload\env.txt"
)
```

#### **How It Works:**

1. **Automatic Detection**: System checks for missing `.zticks` files in the date range
2. **Automatic Download**: If data is missing, connects to cTrader Open API and downloads it
3. **OAuth Authentication**: Handles token refresh and re-authentication automatically
4. **Standard Format**: Saves data in cTrader's native `.zticks` format

#### **Cache Structure:**

```
C:\Users\{YourUsername}\AppData\Roaming\Spotware\Cache\Spotware\BacktestingCache\V1\
  └── demo_19011fd1\          # Account folder (computed from account ID hash)
      └── AUDNZD\             # Symbol name
          └── t1\             # Tick data folder
              ├── 20251124.zticks
              ├── 20251125.zticks
              └── ...
```

#### **Account Folder Naming:**

The account folder name is computed as: `{environment}_{hash}`
- `environment`: "demo" or "live"
- `hash`: First 8 characters of MD5 hash of the `ctidTraderAccountId`

Example: Account ID 5166098 → `demo_19011fd1`

#### **Credentials File (env.txt):**

```ini
# cTrader ID Credentials
CTRADER_USERNAME=YourUsername
CTRADER_PASSWORD=YourPassword

# Trading Account ID (visible in cTrader)
CTRADER_ACCOUNT_ID=5166098

# OAuth Tokens (auto-updated by the system)
CTRADER_ACCESS_TOKEN=...
CTRADER_REFRESH_TOKEN=...
```

**Note:** The `env.txt` file is ONLY used for authentication credentials, NOT for path configuration. The system always uses the standard cTrader cache location on the C: drive.

#### **Key Differences from QuantConnect:**

| Aspect | QuantConnect | cTrader Cache |
|--------|--------------|---------------|
| **Data Location** | G: drive (configurable) | C: drive (standard location) |
| **Data Format** | ZIP files with CSV | GZIP files with binary ticks |
| **Download** | Manual | Automatic on-demand |
| **Resolution** | Minute bars | Raw ticks |
| **Provider Class** | `QuoteQuantConnect` | `QuoteCtraderCache` |

---

## 🔄 **Switching Between Data Providers:**

### **Use QuantConnect:**
```python
from BrokerProvider.QuoteQuantConnect import QuoteQuantConnect

self.robot.DataPath = r"G:\...\QuantConnect Seconds"
self.robot.quote_provider = QuoteQuantConnect(data_rate=60, parameter=self.robot.DataPath)
```

### **Use cTrader Cache:**
```python
from BrokerProvider.QuoteCtraderCache import QuoteCtraderCache

self.robot.DataPath = r"C:\Users\{User}\AppData\Roaming\Spotware\Cache\Spotware\BacktestingCache\V1\demo_19011fd1"
self.robot.quote_provider = QuoteCtraderCache(
    data_rate=0,
    parameter=self.robot.DataPath,
    credentials=r"C:\...\PyDownload\env.txt"
)
```

---

## 🎯 **Best Practices:**

1. **For Production Backtests**: Use cTrader cache for highest fidelity tick data
2. **For Quick Tests**: Use QuantConnect minute data for faster execution
3. **Credentials Security**: Keep `env.txt` secure and never commit it to version control
4. **Path Consistency**: Always use the standard cTrader cache location (C: drive)
5. **Automatic Updates**: Let the system handle OAuth token refresh automatically

