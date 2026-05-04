$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$runner = Join-Path $projectRoot "scripts\run_daily_brief.ps1"

if (-not (Test-Path $runner)) {
    throw "Could not find $runner."
}

$taskName = "DailyBriefAgent"
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$runner`"" `
    -WorkingDirectory $projectRoot
$trigger = New-ScheduledTaskTrigger -Daily -At 7:00am
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Send Shivz Daily Brief by email every morning." `
    -Force | Out-Null

Write-Host "Registered scheduled task '$taskName' for 07:00 daily."
Write-Host "Run logs will be written to $projectRoot\logs."
