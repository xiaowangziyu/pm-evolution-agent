# Setup scheduled tasks - Run as Administrator
# File: setup_tasks.ps1
# Run: Right-click > "Run with PowerShell" (or from admin PowerShell)

$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot

Write-Host "========================================"
Write-Host "Setup Scheduled Tasks"
Write-Host "========================================"
Write-Host ""

$smokeBat = Join-Path $projectRoot "run_smoke.bat"
$fullBat  = Join-Path $projectRoot "run_full.bat"

Write-Host "Project root: $projectRoot"
Write-Host "Smoke bat   : $smokeBat"
Write-Host "Full bat    : $fullBat"
Write-Host ""

# Smoke Test: daily at 20:00
$action1 = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$smokeBat`" auto"
$trigger1 = New-ScheduledTaskTrigger -Daily -At "20:00"
$settings1 = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$principal1 = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

Write-Host "[1/2] Creating Smoke Test task (daily 20:00)..."
try {
    $existing1 = Get-ScheduledTask -TaskName "PM-SmokeTest" -ErrorAction SilentlyContinue
    if ($existing1) { Unregister-ScheduledTask -TaskName "PM-SmokeTest" -Confirm:$false }
    Register-ScheduledTask -TaskName "PM-SmokeTest" -Action $action1 -Trigger $trigger1 -Settings $settings1 -Principal $principal1 | Out-Null
    Write-Host "  [OK] PM-SmokeTest created"
} catch {
    Write-Host "  [FAIL] $_"
}

# Full Test: weekly Sunday at 20:30
$action2 = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$fullBat`" auto"
$trigger2 = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At "20:30"
$settings2 = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$principal2 = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

Write-Host "[2/2] Creating Full Test task (weekly Sunday 20:30)..."
try {
    $existing2 = Get-ScheduledTask -TaskName "PM-FullTest" -ErrorAction SilentlyContinue
    if ($existing2) { Unregister-ScheduledTask -TaskName "PM-FullTest" -Confirm:$false }
    Register-ScheduledTask -TaskName "PM-FullTest" -Action $action2 -Trigger $trigger2 -Settings $settings2 -Principal $principal2 | Out-Null
    Write-Host "  [OK] PM-FullTest created"
} catch {
    Write-Host "  [FAIL] $_"
}

# Verify
Write-Host ""
Write-Host "========================================"
Write-Host "Current tasks:"
Write-Host "========================================"
Get-ScheduledTask | Where-Object { $_.TaskName -in @("PM-SmokeTest", "PM-FullTest") } | ForEach-Object {
    $info = Get-ScheduledTaskInfo -TaskName $_.TaskName
    Write-Host "Name   : $($_.TaskName)"
    Write-Host "State  : $($_.State)"
    Write-Host "NextRun: $($info.NextRunTime)"
    Write-Host ""
}

Write-Host "Done. You can also run taskschd.msc to view/edit tasks."
