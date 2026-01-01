# BTGymProject Cleanup Script
# Run this after closing Visual Studio and Cursor

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "BTGymProject Cleanup Script" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if BTGymProject exists
$btgymPath = "C:\Users\HMz\Documents\BTGymProject"
$archivePath = "C:\Users\HMz\Documents\Archive"
$archivedProject = "$archivePath\BTGymProject_ARCHIVED_2025-10-12"

if (Test-Path $btgymPath) {
    Write-Host "Found BTGymProject (274.4 MB)" -ForegroundColor Yellow
    Write-Host ""
    
    # Create Archive directory
    if (-not (Test-Path $archivePath)) {
        New-Item -ItemType Directory -Path $archivePath | Out-Null
        Write-Host "Created Archive directory" -ForegroundColor Green
    }
    
    # Ask user
    Write-Host "What would you like to do?" -ForegroundColor Cyan
    Write-Host "  [A] Archive - Move to Archive folder (RECOMMENDED)" -ForegroundColor Green
    Write-Host "  [D] Delete - Permanently delete BTGymProject" -ForegroundColor Red
    Write-Host "  [K] Keep - Do nothing, keep as is" -ForegroundColor Yellow
    Write-Host ""
    
    $choice = Read-Host "Enter choice (A/D/K)"
    
    switch ($choice.ToUpper()) {
        "A" {
            Write-Host ""
            Write-Host "Archiving BTGymProject..." -ForegroundColor Yellow
            
            try {
                Move-Item $btgymPath $archivedProject -Force
                Write-Host "✅ SUCCESS: BTGymProject moved to:" -ForegroundColor Green
                Write-Host "   $archivedProject" -ForegroundColor Green
                Write-Host ""
                Write-Host "You can delete it later if not needed." -ForegroundColor Gray
            }
            catch {
                Write-Host "❌ ERROR: Could not move folder" -ForegroundColor Red
                Write-Host "Please close Visual Studio, Cursor, and any file explorers" -ForegroundColor Yellow
                Write-Host "Then run this script again." -ForegroundColor Yellow
            }
        }
        "D" {
            Write-Host ""
            Write-Host "⚠️  WARNING: This will permanently delete BTGymProject!" -ForegroundColor Red
            $confirm = Read-Host "Type 'DELETE' to confirm"
            
            if ($confirm -eq "DELETE") {
                try {
                    Remove-Item $btgymPath -Recurse -Force
                    Write-Host "✅ SUCCESS: BTGymProject deleted" -ForegroundColor Green
                    Write-Host "Freed 274.4 MB of disk space" -ForegroundColor Green
                }
                catch {
                    Write-Host "❌ ERROR: Could not delete folder" -ForegroundColor Red
                    Write-Host "Please close Visual Studio, Cursor, and any file explorers" -ForegroundColor Yellow
                }
            }
            else {
                Write-Host "Deletion cancelled." -ForegroundColor Yellow
            }
        }
        "K" {
            Write-Host ""
            Write-Host "BTGymProject kept as is." -ForegroundColor Yellow
        }
        default {
            Write-Host ""
            Write-Host "Invalid choice. BTGymProject kept as is." -ForegroundColor Yellow
        }
    }
}
else {
    Write-Host "BTGymProject not found (already moved/deleted?)" -ForegroundColor Green
}

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "Cleanup Summary:" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "✅ Uninstalled packages: backtrader, pyzmq, logbook, gym-notices" -ForegroundColor Green
Write-Host "✅ Active project: KitaTrader" -ForegroundColor Green
Write-Host "✅ All code migrated to KitaTrader" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

