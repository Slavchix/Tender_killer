param(
    [int]$ApiPort = $(if ($env:TENDER_KILLER_API_PORT) { [int]$env:TENDER_KILLER_API_PORT } else { 8000 }),
    [int]$WebPort = $(if ($env:TENDER_KILLER_WEB_PORT) { [int]$env:TENDER_KILLER_WEB_PORT } else { 5175 }),
    [int]$TimeoutSeconds = 12
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    throw "Python venv not found: $python"
}

& $python -m tender_killer.dev_control restart `
    --root $root `
    --api-port $ApiPort `
    --web-port $WebPort `
    --timeout-seconds $TimeoutSeconds
exit $LASTEXITCODE
