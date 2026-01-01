# 🧹 BTGymProject Cleanup Instructions

## ⚠️ **Current Issue:**

The BTGymProject folder is **locked** by a running process (likely Cursor editor).

**Error:** "Der Prozess kann nicht auf die Datei zugreifen, da sie bereits von einem anderen Prozess verwendet wird."  
**Translation:** "The process cannot access the file because it is being used by another process."

---

## 🔧 **Solution - Close Everything:**

### **Step 1: Close Cursor Completely**
1. ✅ Close **all Cursor windows**
2. ✅ Check system tray for Cursor icon - **right-click → Quit**
3. ✅ Open Task Manager (Ctrl+Shift+Esc)
4. ✅ Look for "Cursor.exe" processes - **End Task** on all

### **Step 2: Close File Explorer**
1. ✅ Close any File Explorer windows showing BTGymProject
2. ✅ Check if any terminals are in BTGymProject directory

### **Step 3: Run Cleanup**

**Option A: Use Interactive Script** ⭐ **RECOMMENDED**
```powershell
cd C:\Users\HMz\Documents\Source\KitaTrader
.\CLEANUP_OLD_PROJECT.ps1
```

**Option B: Manual Command**
```powershell
Move-Item "C:\Users\HMz\Documents\BTGymProject" "C:\Users\HMz\Documents\Archive\BTGymProject_ARCHIVED_2025-10-12" -Force
```

**Option C: Delete Permanently**
```powershell
Remove-Item "C:\Users\HMz\Documents\BTGymProject" -Recurse -Force
```

---

## 📊 **What Will Be Cleaned:**

### **BTGymProject (274.4 MB):**
```
BTGymProject/
├── btgym/                  ~200 MB (package, not needed)
├── btgym_env/              ~50 MB (venv, not needed)
├── examples/               ~5 MB (old examples)
├── docs/                   ~10 MB (documentation)
├── data/                   ~11 MB (has 6B_seconds_bidask.csv - keep?)
├── *.py files              ~2 MB (all ported to KitaTrader)
└── *.json files            ~1 KB (copied to KitaTrader)
```

### **Files Worth Keeping:**
- `data/6B_seconds_bidask.csv` - 11 MB historical data
  - **Status:** You have this in KitaTrader via Dukascopy (can re-download)
  - **Decision:** Not critical, can be deleted

---

## ✅ **After Cleanup:**

You'll have:
```
C:\Users\HMz\Documents\
├── Archive/
│   └── BTGymProject_ARCHIVED_2025-10-12/  (274 MB, for reference)
│
└── Source/
    └── KitaTrader/  ✅ ACTIVE PROJECT
        ├── Robots/Ultron.py
        ├── Optimizers/
        ├── Environments/
        ├── MainUltron.py
        └── optimizer_config.json
```

---

## 🎯 **Verification After Cleanup:**

Run these to verify everything works:

```bash
cd C:\Users\HMz\Documents\Source\KitaTrader
python -c "from Robots.Ultron import Ultron; print('✅ Ultron OK')"
python -c "import json; print('✅ Config:', json.load(open('optimizer_config.json'))['data']['symbol'])"
```

---

## 💡 **If Still Locked:**

Try the **robocopy** method (works even with locks):

```powershell
# Copy to Archive
robocopy "C:\Users\HMz\Documents\BTGymProject" "C:\Users\HMz\Documents\Archive\BTGymProject_ARCHIVED_2025-10-12" /E /MOVE

# Or just delete
rd /s /q "C:\Users\HMz\Documents\BTGymProject"
```

---

## 🚀 **What's Next:**

Once cleanup is done:

1. **Test KitaTrader:**
   ```bash
   python MainUltron.py
   ```

2. **Set as Visual Studio startup:**
   - Open `KitaTrader.sln` in Visual Studio
   - Set `MainUltron.py` as startup file
   - Press F5 to debug

3. **Start optimizing:**
   ```bash
   python Optimizers/GeneticOptimizer.py
   ```

---

**Current Working Directory:** `C:\Users\HMz\Documents\Source\KitaTrader` ✅

**Context:** FULLY PRESERVED ✅

**Ready when you are!** 🎯

