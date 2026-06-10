# Check scheduled tasks
Get-ScheduledTask | Where-Object { $_.TaskName -in @("PM-SmokeTest", "PM-FullTest") } | ForEach-Object {
    $info = Get-ScheduledTaskInfo -TaskName $_.TaskName
    Write-Host "Name   : $($_.TaskName)"
    Write-Host "State  : $($_.State)"
    Write-Host "NextRun: $($info.NextRunTime)"
    Write-Host ""
}
if (-not (Get-ScheduledTask -TaskName "PM-SmokeTest" -ErrorAction SilentlyContinue)) {
    Write-Host "[WARN] PM-SmokeTest not found"
}
if (-not (Get-ScheduledTask -TaskName "PM-FullTest" -ErrorAction SilentlyContinue)) {
    Write-Host "[WARN] PM-FullTest not found"
}
