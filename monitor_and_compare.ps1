# Monitor Python bot log and run comparison when ready
param(
    [string]$csharpLog = "C:\Users\HMz\Documents\cAlgo\Data\cBots\OHLCTestBot\29639f65-52c0-4443-a8c7-b6511867444a\Backtesting\log.txt",
    [string]$pythonLog = "C:\Users\HMz\Documents\cAlgo\Logfiles\OHLCTestBot_Python.log",
    [int]$checkIntervalSeconds = 10,
    [int]$maxWaitMinutes = 60
)

$startTime = Get-Date
Write-Output "=== MONITORING PYTHON BOT FOR INDICATOR LOGGING ==="
Write-Output "Start time: $startTime"
Write-Output "C# log: $csharpLog"
Write-Output "Python log: $pythonLog"
Write-Output "Check interval: $checkIntervalSeconds seconds"
Write-Output "Max wait time: $maxWaitMinutes minutes"
Write-Output ""

$maxWaitSeconds = $maxWaitMinutes * 60
$elapsed = 0
$lastBarCount = 0
$lastIndCount = 0
$lastFileModTime = $null
$lastProgressTime = Get-Date
$stallThresholdSeconds = 120  # Alert if no progress for 2 minutes
$checkCount = 0

while ($elapsed -lt $maxWaitSeconds) {
    $checkCount++
    $currentTime = Get-Date
    $elapsed = ($currentTime - $startTime).TotalSeconds
    
    if (Test-Path $pythonLog) {
        try {
            $file = Get-Item $pythonLog
            $fileModTime = $file.LastWriteTime
            $content = Get-Content $pythonLog -ErrorAction SilentlyContinue
            $indCount = ($content | Select-String "FINAL_IND").Count
            $barCount = ($content | Select-String "FINAL_BAR").Count
            
            # Detect progress: file modified, bar count increased, or indicator count increased
            $fileUpdated = ($null -eq $lastFileModTime -or $fileModTime -gt $lastFileModTime)
            $barsIncreased = $barCount -gt $lastBarCount
            $indsIncreased = $indCount -gt $lastIndCount
            $hasProgress = $fileUpdated -or $barsIncreased -or $indsIncreased
            
            if ($hasProgress) {
                $lastProgressTime = $currentTime
            }
            
            # Calculate time since last progress
            $timeSinceProgress = ($currentTime - $lastProgressTime).TotalSeconds
            $timeSinceFileUpdate = if ($fileModTime) { ($currentTime - $fileModTime).TotalSeconds } else { 0 }
            
            # Determine status icon
            $statusIcon = if ($barsIncreased -or $indsIncreased) { "[OK]" } 
                         elseif ($timeSinceProgress -gt $stallThresholdSeconds) { "[WARN]" } 
                         elseif ($fileUpdated) { "[UPD]" }
                         else { "[*]" }
            
            # Log progress updates immediately with rate
            if ($barsIncreased -or $indsIncreased) {
                $rateInfo = ""
                if ($barsIncreased) { 
                    $barDelta = $barCount - $lastBarCount
                    $timeDelta = if ($lastFileModTime) { ($fileModTime - $lastFileModTime).TotalSeconds } else { $checkIntervalSeconds }
                    if ($timeDelta -gt 0) { 
                        $rate = [math]::Round($barDelta / $timeDelta, 1)
                        $rateInfo = " | Rate: " + $rate.ToString()
                    }
                }
                
                Write-Output "[$($currentTime.ToString('HH:mm:ss'))] [OK] PROGRESS | Elapsed: $([math]::Round($elapsed/60, 1))m | Bars: $barCount (+$($barCount - $lastBarCount)) | Inds: $indCount (+$($indCount - $lastIndCount))$rateInfo"
                $lastBarCount = $barCount
                $lastIndCount = $indCount
            }
            
            # Heartbeat status message every check (10 seconds)
            $statusText = if ($timeSinceProgress -gt $stallThresholdSeconds) { "STALLED" } 
                         elseif ($fileUpdated) { "UPDATED" }
                         else { "HEARTBEAT" }
            
            Write-Output "[$($currentTime.ToString('HH:mm:ss'))] $statusIcon $statusText | Elapsed: $([math]::Round($elapsed/60, 1))m | Bars: $barCount | Inds: $indCount | Last update: $([math]::Round($timeSinceFileUpdate, 0))s ago | No progress: $([math]::Round($timeSinceProgress, 0))s"
            
            $lastFileModTime = $fileModTime
            
            # Alert if stalled
            if ($timeSinceProgress -gt $stallThresholdSeconds -and $barCount -eq 0) {
                Write-Output ""
                Write-Output "[WARN] WARNING: Bot appears to be stalled!"
                Write-Output "   No progress detected for $([math]::Round($timeSinceProgress, 0)) seconds"
                Write-Output "   Log file exists but no bars have been processed yet."
                Write-Output "   The bot may need to be restarted."
                Write-Output ""
            }
            
            # Check if indicators are ready (need at least some entries)
            if ($indCount -gt 100) {
                Write-Output ""
                Write-Output "[OK] INDICATORS DETECTED! Bot appears to be running with indicator logging."
                Write-Output "   Found $indCount indicator entries. Waiting a bit more to ensure completion..."
                Start-Sleep -Seconds 30  # Wait 30 more seconds to ensure bot finishes
                
                # Final check
                $finalContent = Get-Content $pythonLog -ErrorAction SilentlyContinue
                $finalIndCount = ($finalContent | Select-String "FINAL_IND").Count
                $finalBarCount = ($finalContent | Select-String "FINAL_BAR").Count
                
                Write-Output ""
                Write-Output "=== FINAL STATUS ==="
                Write-Output "Bars: $finalBarCount"
                Write-Output "Indicators: $finalIndCount"
                Write-Output ""
                
                if ($finalIndCount -gt 0) {
                    Write-Output "[OK] Running comparison test..."
                    Write-Output ""
                    & "$PSScriptRoot\compare_logs.ps1" -csharpLog $csharpLog -pythonLog $pythonLog
                    exit 0
                }
            }
        } catch {
            # Silently continue on errors
        }
    } else {
        # Log file doesn't exist yet - heartbeat showing waiting status
        $timeSinceProgress = ($currentTime - $lastProgressTime).TotalSeconds
        Write-Output "[$($currentTime.ToString('HH:mm:ss'))] [*] HEARTBEAT | Elapsed: $([math]::Round($elapsed/60, 1))m | Log file: NOT FOUND | Waiting for bot to create log file..."
    }
    
    Start-Sleep -Seconds $checkIntervalSeconds
    $elapsed = ($(Get-Date) - $startTime).TotalSeconds
}

Write-Output ""
Write-Output "[TIMEOUT] Timeout reached after $maxWaitMinutes minutes."
Write-Output "Checking final status..."
if (Test-Path $pythonLog) {
    $content = Get-Content $pythonLog -ErrorAction SilentlyContinue
    $indCount = ($content | Select-String "FINAL_IND").Count
    $barCount = ($content | Select-String "FINAL_BAR").Count
    Write-Output "Final status - Bars: $barCount, Indicators: $indCount"
    
    if ($indCount -gt 0) {
        Write-Output ""
        Write-Output "✅ Running comparison test..."
        Write-Output ""
        & "$PSScriptRoot\compare_logs.ps1" -csharpLog $csharpLog -pythonLog $pythonLog
    } else {
        Write-Output ""
        Write-Output "[ERR] No indicators found. Python bot may need to be re-run with updated code."
    }
}
