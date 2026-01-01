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

