# Compare Kanga2 CSV logs from C# and Python
param(
    [string]$csharpLog = "",
    [string]$pythonLog = ""
)

# Default paths
if ([string]::IsNullOrEmpty($csharpLog)) {
    # Try to find C# log in typical cTrader output locations
    # 1. Try Backtesting directory (most common)
    $csharpLog = "C:\Users\HMz\Documents\cAlgo\Data\cBots\Kanga2\*\Backtesting\*.csv"
    $csharpFiles = Get-ChildItem -Path $csharpLog -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($csharpFiles) {
        $csharpLog = $csharpFiles.FullName
    } else {
        # 2. Fallback: try in Logfiles directory (exclude Python logs)
        $csharpLog = "C:\Users\HMz\Documents\cAlgo\Logfiles\Kanga2*.csv"
        $csharpFiles = Get-ChildItem -Path $csharpLog -ErrorAction SilentlyContinue | Where-Object { $_.Name -notmatch "_Python" } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($csharpFiles) {
            $csharpLog = $csharpFiles.FullName
        }
    }
}

if ([string]::IsNullOrEmpty($pythonLog)) {
    # Try to find Python log in typical output location
    $pythonLog = "C:\Users\HMz\Documents\cAlgo\Logfiles\*Python*.csv"
    $pythonFiles = Get-ChildItem -Path $pythonLog -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($pythonFiles) {
        $pythonLog = $pythonFiles.FullName
    }
}

Write-Output "=== KANGA2 LOG COMPARISON ==="
Write-Output ""
Write-Output "C# Log: $csharpLog"
Write-Output "Python Log: $pythonLog"
Write-Output ""

if (-not (Test-Path $csharpLog)) {
    Write-Output "ERROR: C# log file not found: $csharpLog"
    exit 1
}

if (-not (Test-Path $pythonLog)) {
    Write-Output "ERROR: Python log file not found: $pythonLog"
    exit 1
}

# Read CSV files
Write-Output "=== READING LOG FILES ==="
$csharpContent = Get-Content $csharpLog -Encoding UTF8
$pythonContent = Get-Content $pythonLog -Encoding UTF8

Write-Output "C# log lines: $($csharpContent.Count)"
Write-Output "Python log lines: $($pythonContent.Count)"
Write-Output ""

# Parse CSV (skip header lines starting with "sep=")
$csharpTrades = @()
$pythonTrades = @()

foreach ($line in $csharpContent) {
    if ($line -match "^sep=") { continue }
    if ($line -match "^Number,") { continue }  # Skip header
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    if ($line -match "^Backtest completed") { break }  # Stop at stats section
    
    $fields = $line -split ","
    if ($fields.Count -ge 12) {
        $csharpTrades += @{
            Number = $fields[0]
            NetProfit = [double]$fields[1]
            Symbol = $fields[2]
            Mode = $fields[3]
            Lots = [double]$fields[4]
            OpenDate = $fields[5]
            CloseDate = $fields[6]
            OpenPrice = [double]$fields[7]
            ClosePrice = [double]$fields[8]
            BollingerUpper = [double]$fields[9]
            BollingerLower = [double]$fields[10]
            BollingerMain = [double]$fields[11]
            Key = "$($fields[2])|$($fields[5])|$($fields[6])|$($fields[3])"
        }
    }
}

foreach ($line in $pythonContent) {
    if ($line -match "^sep=") { continue }
    if ($line -match "^Number,") { continue }  # Skip header
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    if ($line -match "^Backtest completed") { break }  # Stop at stats section
    
    $fields = $line -split ","
    if ($fields.Count -ge 12) {
        $pythonTrades += @{
            Number = $fields[0]
            NetProfit = [double]$fields[1]
            Symbol = $fields[2]
            Mode = $fields[3]
            Lots = [double]$fields[4]
            OpenDate = $fields[5]
            CloseDate = $fields[6]
            OpenPrice = [double]$fields[7]
            ClosePrice = [double]$fields[8]
            BollingerUpper = [double]$fields[9]
            BollingerLower = [double]$fields[10]
            BollingerMain = [double]$fields[11]
            Key = "$($fields[2])|$($fields[5])|$($fields[6])|$($fields[3])"
        }
    }
}

Write-Output "=== TRADE COUNT ==="
Write-Output "C# trades: $($csharpTrades.Count)"
Write-Output "Python trades: $($pythonTrades.Count)"
Write-Output ""

# Create lookup dictionaries
$csharpDict = @{}
foreach ($trade in $csharpTrades) {
    $csharpDict[$trade.Key] = $trade
}

$pythonDict = @{}
foreach ($trade in $pythonTrades) {
    $pythonDict[$trade.Key] = $trade
}

# Find common and unique trades
$commonKeys = @()
$csharpOnly = @()
$pythonOnly = @()

foreach ($key in $csharpDict.Keys) {
    if ($pythonDict.ContainsKey($key)) {
        $commonKeys += $key
    } else {
        $csharpOnly += $key
    }
}

foreach ($key in $pythonDict.Keys) {
    if (-not $csharpDict.ContainsKey($key)) {
        $pythonOnly += $key
    }
}

Write-Output "=== COMPARISON RESULTS ==="
Write-Output "Common trades: $($commonKeys.Count)"
Write-Output "C# only: $($csharpOnly.Count)"
Write-Output "Python only: $($pythonOnly.Count)"
Write-Output ""

# Compare common trades
$matching = 0
$mismatching = 0
$mismatches = @()

foreach ($key in $commonKeys) {
    $cs = $csharpDict[$key]
    $py = $pythonDict[$key]
    
    $match = $true
    $diff = @{}
    
    # Compare NetProfit (allow small difference due to rounding)
    if ([Math]::Abs($cs.NetProfit - $py.NetProfit) -gt 0.01) {
        $match = $false
        $diff["NetProfit"] = "C#=$($cs.NetProfit), Python=$($py.NetProfit)"
    }
    
    # Compare Lots
    if ([Math]::Abs($cs.Lots - $py.Lots) -gt 0.01) {
        $match = $false
        $diff["Lots"] = "C#=$($cs.Lots), Python=$($py.Lots)"
    }
    
    # Compare OpenPrice (allow small difference)
    if ([Math]::Abs($cs.OpenPrice - $py.OpenPrice) -gt 0.00001) {
        $match = $false
        $diff["OpenPrice"] = "C#=$($cs.OpenPrice), Python=$($py.OpenPrice)"
    }
    
    # Compare ClosePrice (allow small difference)
    if ([Math]::Abs($cs.ClosePrice - $py.ClosePrice) -gt 0.00001) {
        $match = $false
        $diff["ClosePrice"] = "C#=$($cs.ClosePrice), Python=$($py.ClosePrice)"
    }
    
    if ($match) {
        $matching++
    } else {
        $mismatching++
        $mismatches += @{
            Key = $key
            Trade = $cs
            Differences = $diff
        }
    }
}

Write-Output "=== TRADE DETAIL COMPARISON ==="
Write-Output "Matching trades: $matching"
Write-Output "Mismatching trades: $mismatching"
if ($commonKeys.Count -gt 0) {
    $matchRate = [Math]::Round(($matching / $commonKeys.Count) * 100, 2)
    Write-Output "Match rate: $matchRate%"
}
Write-Output ""

if ($mismatches.Count -gt 0) {
    Write-Output "=== FIRST 10 MISMATCHES ==="
    $count = [Math]::Min(10, $mismatches.Count)
    for ($i = 0; $i -lt $count; $i++) {
        $m = $mismatches[$i]
        Write-Output "Key: $($m.Key)"
        foreach ($field in $m.Differences.Keys) {
            Write-Output "  $field : $($m.Differences[$field])"
        }
        Write-Output ""
    }
}

if ($csharpOnly.Count -gt 0) {
    Write-Output "=== TRADES ONLY IN C# (First 10) ==="
    $count = [Math]::Min(10, $csharpOnly.Count)
    for ($i = 0; $i -lt $count; $i++) {
        $trade = $csharpDict[$csharpOnly[$i]]
        Write-Output "$($trade.Symbol) | $($trade.OpenDate) | $($trade.CloseDate) | $($trade.Mode) | Profit=$($trade.NetProfit)"
    }
    Write-Output ""
}

if ($pythonOnly.Count -gt 0) {
    Write-Output "=== TRADES ONLY IN PYTHON (First 10) ==="
    $count = [Math]::Min(10, $pythonOnly.Count)
    for ($i = 0; $i -lt $count; $i++) {
        $trade = $pythonDict[$pythonOnly[$i]]
        Write-Output "$($trade.Symbol) | $($trade.OpenDate) | $($trade.CloseDate) | $($trade.Mode) | Profit=$($trade.NetProfit)"
    }
    Write-Output ""
}

# Summary statistics
Write-Output "=== SUMMARY STATISTICS ==="
if ($csharpTrades.Count -gt 0) {
    $csTotalProfit = ($csharpTrades | Measure-Object -Property NetProfit -Sum).Sum
    $csWinning = ($csharpTrades | Where-Object { $_.NetProfit -gt 0 }).Count
    $csLosing = ($csharpTrades | Where-Object { $_.NetProfit -lt 0 }).Count
    Write-Output "C# Total Profit: $csTotalProfit"
    Write-Output "C# Winning Trades: $csWinning"
    Write-Output "C# Losing Trades: $csLosing"
    Write-Output ""
}

if ($pythonTrades.Count -gt 0) {
    $pyTotalProfit = ($pythonTrades | Measure-Object -Property NetProfit -Sum).Sum
    $pyWinning = ($pythonTrades | Where-Object { $_.NetProfit -gt 0 }).Count
    $pyLosing = ($pythonTrades | Where-Object { $_.NetProfit -lt 0 }).Count
    Write-Output "Python Total Profit: $pyTotalProfit"
    Write-Output "Python Winning Trades: $pyWinning"
    Write-Output "Python Losing Trades: $pyLosing"
    Write-Output ""
}
