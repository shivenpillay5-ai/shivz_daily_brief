$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
$logDir = Join-Path $projectRoot "logs"

if (-not (Test-Path $python)) {
    throw "Could not find $python. Create the virtual environment first."
}

if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$logFile = Join-Path $logDir "daily-brief-$timestamp.log"

Set-Location $projectRoot

try {
    "Starting Shivz Daily Brief at $(Get-Date -Format o)" | Tee-Object -FilePath $logFile
    & $python -m daily_brief.main --send --no-openai *>&1 | Tee-Object -FilePath $logFile -Append
    "Finished Shivz Daily Brief at $(Get-Date -Format o)" | Tee-Object -FilePath $logFile -Append
}
catch {
    "Failed Shivz Daily Brief at $(Get-Date -Format o)" | Tee-Object -FilePath $logFile -Append
    $_ | Out-String | Tee-Object -FilePath $logFile -Append
    throw
}

