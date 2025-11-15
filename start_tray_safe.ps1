# Safe startup script for Label Print Server
# Ensures clean startup by killing existing processes and cleaning up files

$appDir = "c:\Users\Gokul\Desktop\PROGRAM FILES\Label-print-server"
Set-Location $appDir

Write-Host "========================================"
Write-Host "  Label Print Server - Safe Startup"
Write-Host "========================================`n"

# Step 1: Kill existing processes
Write-Host "[1/4] Checking for existing processes..."
$processes = Get-Process | Where-Object { $_.Path -like "*Label-print-server*.venv*python*" }
if ($processes) {
    foreach ($proc in $processes) {
        Write-Host "  Stopping process $($proc.Id)..."
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "  Stopped $($processes.Count) process(es)"
} else {
    Write-Host "  No existing processes found"
}

# Step 2: Clean up control files
Write-Host "`n[2/4] Cleaning up control files..."
$cleaned = 0
Get-ChildItem $appDir -Filter ".tray_*" -Force -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
    $cleaned++
}
Write-Host "  Removed $cleaned control file(s)"

# Step 3: Wait for cleanup
Write-Host "`n[3/4] Waiting for cleanup..."
Start-Sleep -Seconds 2

# Step 4: Start tray app
Write-Host "`n[4/4] Starting tray app..."
$pythonw = Join-Path $appDir ".venv\Scripts\pythonw.exe"
$trayScript = Join-Path $appDir "tray_app.py"

if (Test-Path $pythonw) {
    Start-Process $pythonw -ArgumentList $trayScript -WindowStyle Hidden
    Start-Sleep -Seconds 2
    
    # Verify it started
    $running = Get-Process | Where-Object { $_.Path -eq $pythonw }
    if ($running) {
        Write-Host "`n✓ Tray app started successfully!"
        Write-Host "  Check your system tray for the icon.`n"
    } else {
        Write-Host "`n✗ Tray app may not have started. Check logs for errors.`n"
    }
} else {
    Write-Host "`n✗ Python executable not found at: $pythonw"
    Write-Host "  Please run setup.bat first.`n"
}

Write-Host "========================================"
