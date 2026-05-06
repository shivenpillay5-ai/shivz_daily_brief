param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("daily-brief", "daily-devotional", "team-shinola-brief")]
    [string]$EventType,

    [string]$Owner = "shivenpillay5-ai",
    [string]$Repo = "shivz_daily_brief",
    [string]$Token = $env:GITHUB_DISPATCH_TOKEN
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Token)) {
    throw "Set GITHUB_DISPATCH_TOKEN to a fine-grained GitHub token with Contents read/write access to $Owner/$Repo."
}

$headers = @{
    "Accept" = "application/vnd.github+json"
    "Authorization" = "Bearer $Token"
    "X-GitHub-Api-Version" = "2022-11-28"
}

$body = @{
    event_type = $EventType
    client_payload = @{
        source = "manual-powershell"
    }
} | ConvertTo-Json -Depth 4

$uri = "https://api.github.com/repos/$Owner/$Repo/dispatches"
Invoke-RestMethod -Method Post -Uri $uri -Headers $headers -ContentType "application/json" -Body $body

Write-Host "Dispatched '$EventType' to $Owner/$Repo."
