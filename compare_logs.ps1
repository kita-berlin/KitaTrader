# Compare C# and Python OHLCTestBot log files (bars and indicators)
param(
    [string]$csharpLog = "C:\Users\HMz\Documents\cAlgo\Data\cBots\OHLCTestBot\29639f65-52c0-4443-a8c7-b6511867444a\Backtesting\log.txt",
    [string]$pythonLog = "C:\Users\HMz\Documents\cAlgo\Logfiles\OHLCTestBot_Python.log"
)

if (-not (Test-Path $csharpLog)) {
    Write-Output "ERROR: C# log file not found: $csharpLog"
    exit 1
}

if (-not (Test-Path $pythonLog)) {
    Write-Output "ERROR: Python log file not found: $pythonLog"
    exit 1
}

Write-Output "=== READING LOG FILES ==="
$csharpContent = Get-Content $csharpLog
$pythonContent = Get-Content $pythonLog
Write-Output "C# log lines: $($csharpContent.Count)"
Write-Output "Python log lines: $($pythonContent.Count)"
Write-Output ""

Write-Output "=== EXTRACTING FINAL_BAR ENTRIES ==="
$csharpBars = $csharpContent | Select-String "FINAL_BAR"
$pythonBars = $pythonContent | Select-String "FINAL_BAR"
Write-Output "C# FINAL_BAR entries: $($csharpBars.Count)"
Write-Output "Python FINAL_BAR entries: $($pythonBars.Count)"
Write-Output ""

# Extract just the FINAL_BAR line content (without timestamp prefix)
$csharpBarLines = $csharpBars | ForEach-Object { 
    $line = $_.Line
    if ($line -match "FINAL_BAR\|(.+)") {
        "FINAL_BAR|$($matches[1])"
    } else {
        $line -replace "^.*?FINAL_BAR", "FINAL_BAR"
    }
}

$pythonBarLines = $pythonBars | ForEach-Object {
    $line = $_.Line
    if ($line -match "FINAL_BAR\|(.+)") {
        "FINAL_BAR|$($matches[1])"
    } else {
        $line -replace "^.*?FINAL_BAR", "FINAL_BAR"
    }
}

Write-Output "=== COMPARISON ==="
Write-Output "C# bars (cleaned): $($csharpBarLines.Count)"
Write-Output "Python bars (cleaned): $($pythonBarLines.Count)"
Write-Output ""

# Create dictionaries keyed by timeframe and timestamp
$csharpDict = @{}
$pythonDict = @{}

foreach ($line in $csharpBarLines) {
    $parts = $line -split "\|"
    if ($parts.Count -ge 3) {
        $key = "$($parts[0])|$($parts[1])|$($parts[2])"  # FINAL_BAR|TF|Timestamp
        $csharpDict[$key] = $line
    }
}

foreach ($line in $pythonBarLines) {
    $parts = $line -split "\|"
    if ($parts.Count -ge 3) {
        $key = "$($parts[0])|$($parts[1])|$($parts[2])"  # FINAL_BAR|TF|Timestamp
        $pythonDict[$key] = $line
    }
}

Write-Output "=== UNIQUE KEYS ==="
Write-Output "C# unique keys: $($csharpDict.Keys.Count)"
Write-Output "Python unique keys: $($pythonDict.Keys.Count)"
Write-Output ""

# Find common keys
$commonKeys = @()
foreach ($key in $csharpDict.Keys) {
    if ($pythonDict.ContainsKey($key)) {
        $commonKeys += $key
    }
}

Write-Output "Common keys (bars in both): $($commonKeys.Count)"
Write-Output ""

# Compare values for common keys
$matches = 0
$mismatches = 0
$mismatchDetails = @()

foreach ($key in $commonKeys) {
    $csharpValue = $csharpDict[$key]
    $pythonValue = $pythonDict[$key]
    
    if ($csharpValue -eq $pythonValue) {
        $matches++
    } else {
        $mismatches++
        if ($mismatches -le 20) {
            $mismatchDetails += "Key: $key"
            $mismatchDetails += "  C#:    $csharpValue"
            $mismatchDetails += "  Python: $pythonValue"
            $mismatchDetails += ""
        }
    }
}

Write-Output "=== COMPARISON RESULTS ==="
Write-Output "Matching bars: $matches"
Write-Output "Mismatching bars: $mismatches"
if ($commonKeys.Count -gt 0) {
    $matchRate = [math]::Round(($matches / $commonKeys.Count) * 100, 2)
    Write-Output "Match rate: $matchRate%"
}
Write-Output ""

# Find bars only in C#
$onlyCSharp = @()
foreach ($key in $csharpDict.Keys) {
    if (-not $pythonDict.ContainsKey($key)) {
        $onlyCSharp += $key
    }
}

# Find bars only in Python
$onlyPython = @()
foreach ($key in $pythonDict.Keys) {
    if (-not $csharpDict.ContainsKey($key)) {
        $onlyPython += $key
    }
}

Write-Output "=== BARS ONLY IN C# ==="
Write-Output "Count: $($onlyCSharp.Count)"
if ($onlyCSharp.Count -gt 0 -and $onlyCSharp.Count -le 10) {
    $onlyCSharp | ForEach-Object { Write-Output "  $_" }
} elseif ($onlyCSharp.Count -gt 10) {
    Write-Output "First 10:"
    $onlyCSharp | Select-Object -First 10 | ForEach-Object { Write-Output "  $_" }
}
Write-Output ""

Write-Output "=== BARS ONLY IN PYTHON ==="
Write-Output "Count: $($onlyPython.Count)"
if ($onlyPython.Count -gt 0 -and $onlyPython.Count -le 10) {
    $onlyPython | ForEach-Object { Write-Output "  $_" }
} elseif ($onlyPython.Count -gt 10) {
    Write-Output "First 10:"
    $onlyPython | Select-Object -First 10 | ForEach-Object { Write-Output "  $_" }
}
Write-Output ""

if ($mismatches -gt 0) {
    Write-Output "=== FIRST 20 MISMATCHES ==="
    $mismatchDetails | Select-Object -First 20
    Write-Output ""
}

# Breakdown by timeframe
Write-Output "=== BREAKDOWN BY TIMEFRAME ==="
$timeframes = @("M1", "M5", "H1", "H4")
foreach ($tf in $timeframes) {
    $csharpTF = ($csharpBarLines | Where-Object { $_ -match "FINAL_BAR\|$tf\|" }).Count
    $pythonTF = ($pythonBarLines | Where-Object { $_ -match "FINAL_BAR\|$tf\|" }).Count
    $commonTF = ($commonKeys | Where-Object { $_ -match "FINAL_BAR\|$tf\|" }).Count
    Write-Output "$tf : C#=$csharpTF, Python=$pythonTF, Common=$commonTF"
}

Write-Output ""
Write-Output "=== SAMPLE COMPARISON (First 10 common bars) ==="
$sampleKeys = $commonKeys | Select-Object -First 10
foreach ($key in $sampleKeys) {
    $csharpValue = $csharpDict[$key]
    $pythonValue = $pythonDict[$key]
    Write-Output "Key: $key"
    Write-Output "  C#:    $csharpValue"
    Write-Output "  Python: $pythonValue"
    Write-Output "  Match: $(if ($csharpValue -eq $pythonValue) { 'YES' } else { 'NO' })"
    Write-Output ""
}

# ============================================
# INDICATOR COMPARISON
# ============================================
Write-Output ""
Write-Output "============================================"
Write-Output "=== INDICATOR COMPARISON ==="
Write-Output "============================================"
Write-Output ""

Write-Output "=== EXTRACTING FINAL_IND ENTRIES ==="
$csharpInds = $csharpContent | Select-String "FINAL_IND"
$pythonInds = $pythonContent | Select-String "FINAL_IND"
Write-Output "C# FINAL_IND entries: $($csharpInds.Count)"
Write-Output "Python FINAL_IND entries: $($pythonInds.Count)"
Write-Output ""

if ($csharpInds.Count -eq 0 -and $pythonInds.Count -eq 0) {
    Write-Output "WARNING: No indicator entries found in either log file."
    Write-Output "The bots may need to be updated to log indicator values."
    Write-Output ""
} else {
    # Extract indicator lines
    $csharpIndLines = $csharpInds | ForEach-Object { 
        $line = $_.Line
        if ($line -match "FINAL_IND\|(.+)") {
            "FINAL_IND|$($matches[1])"
        } else {
            $line -replace "^.*?FINAL_IND", "FINAL_IND"
        }
    }

    $pythonIndLines = $pythonInds | ForEach-Object {
        $line = $_.Line
        if ($line -match "FINAL_IND\|(.+)") {
            "FINAL_IND|$($matches[1])"
        } else {
            $line -replace "^.*?FINAL_IND", "FINAL_IND"
        }
    }

    Write-Output "C# indicators (cleaned): $($csharpIndLines.Count)"
    Write-Output "Python indicators (cleaned): $($pythonIndLines.Count)"
    Write-Output ""

    # Create dictionaries keyed by timeframe and timestamp
    $csharpIndDict = @{}
    $pythonIndDict = @{}

    foreach ($line in $csharpIndLines) {
        $parts = $line -split "\|"
        if ($parts.Count -ge 3) {
            $key = "$($parts[0])|$($parts[1])|$($parts[2])"  # FINAL_IND|TF|Timestamp
            $csharpIndDict[$key] = $line
        }
    }

    foreach ($line in $pythonIndLines) {
        $parts = $line -split "\|"
        if ($parts.Count -ge 3) {
            $key = "$($parts[0])|$($parts[1])|$($parts[2])"  # FINAL_IND|TF|Timestamp
            $pythonIndDict[$key] = $line
        }
    }

    Write-Output "=== INDICATOR UNIQUE KEYS ==="
    Write-Output "C# unique keys: $($csharpIndDict.Keys.Count)"
    Write-Output "Python unique keys: $($pythonIndDict.Keys.Count)"
    Write-Output ""

    # Find common keys
    $commonIndKeys = @()
    foreach ($key in $csharpIndDict.Keys) {
        if ($pythonIndDict.ContainsKey($key)) {
            $commonIndKeys += $key
        }
    }

    Write-Output "Common indicator keys: $($commonIndKeys.Count)"
    Write-Output ""

    # Compare indicator values
    $indMatches = 0
    $indMismatches = 0
    $indMismatchDetails = @()

    foreach ($key in $commonIndKeys) {
        $csharpValue = $csharpIndDict[$key]
        $pythonValue = $pythonIndDict[$key]
        
        if ($csharpValue -eq $pythonValue) {
            $indMatches++
        } else {
            $indMismatches++
            if ($indMismatches -le 20) {
                $indMismatchDetails += "Key: $key"
                $indMismatchDetails += "  C#:    $csharpValue"
                $indMismatchDetails += "  Python: $pythonValue"
                $indMismatchDetails += ""
            }
        }
    }

    Write-Output "=== INDICATOR COMPARISON RESULTS ==="
    Write-Output "Matching indicators: $indMatches"
    Write-Output "Mismatching indicators: $indMismatches"
    if ($commonIndKeys.Count -gt 0) {
        $indMatchRate = [math]::Round(($indMatches / $commonIndKeys.Count) * 100, 2)
        Write-Output "Match rate: $indMatchRate%"
    }
    Write-Output ""

    # Breakdown by timeframe
    Write-Output "=== INDICATOR BREAKDOWN BY TIMEFRAME ==="
    $timeframes = @("M1", "M5", "H1", "H4")
    foreach ($tf in $timeframes) {
        $csharpTF = ($csharpIndLines | Where-Object { $_ -match "FINAL_IND\|$tf\|" }).Count
        $pythonTF = ($pythonIndLines | Where-Object { $_ -match "FINAL_IND\|$tf\|" }).Count
        $commonTF = ($commonIndKeys | Where-Object { $_ -match "FINAL_IND\|$tf\|" }).Count
        Write-Output "$tf : C#=$csharpTF, Python=$pythonTF, Common=$commonTF"
    }
    Write-Output ""

    if ($indMismatches -gt 0) {
        Write-Output "=== FIRST 20 INDICATOR MISMATCHES ==="
        $indMismatchDetails | Select-Object -First 20
        Write-Output ""
    }

    # Sample comparison
    Write-Output "=== SAMPLE INDICATOR COMPARISON (First 5 common indicators) ==="
    $sampleIndKeys = $commonIndKeys | Select-Object -First 5
    foreach ($key in $sampleIndKeys) {
        $csharpValue = $csharpIndDict[$key]
        $pythonValue = $pythonIndDict[$key]
        Write-Output "Key: $key"
        Write-Output "  C#:    $csharpValue"
        Write-Output "  Python: $pythonValue"
        Write-Output "  Match: $(if ($csharpValue -eq $pythonValue) { 'YES' } else { 'NO' })"
        Write-Output ""
    }
}
