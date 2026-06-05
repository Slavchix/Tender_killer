param(
    [int]$ApiPort = $(if ($env:TENDER_KILLER_API_PORT) { [int]$env:TENDER_KILLER_API_PORT } else { 8000 }),
    [int]$WebPort = $(if ($env:TENDER_KILLER_WEB_PORT) { [int]$env:TENDER_KILLER_WEB_PORT } else { 5175 }),
    [int]$TimeoutSeconds = 12,
    [int[]]$ExtraWebPorts = @(5173, 5174)
)

$ErrorActionPreference = "Stop"

$launcher = Join-Path $PSScriptRoot "restart-dev.mjs"

function Find-Node {
    if ($env:LOCALAPPDATA) {
        $codexBin = Join-Path $env:LOCALAPPDATA "OpenAI\Codex\bin"
        if (Test-Path -LiteralPath $codexBin) {
            $codexNode = Get-ChildItem -Path $codexBin -Recurse -Filter node.exe -ErrorAction SilentlyContinue |
                Sort-Object LastWriteTime -Descending |
                Select-Object -First 1
            if ($codexNode) {
                return $codexNode.FullName
            }
        }
    }
    $node = (Get-Command node.exe -ErrorAction SilentlyContinue).Source
    if ($node) {
        return $node
    }
    return $null
}

if (-not (Test-Path -LiteralPath $launcher)) {
    throw "Restart launcher not found: $launcher"
}

$node = Find-Node
if (-not $node) {
    throw "node.exe not found"
}

$args = @(
    $launcher,
    "--api-port", "$ApiPort",
    "--web-port", "$WebPort",
    "--timeout-seconds", "$TimeoutSeconds"
)
if ($ExtraWebPorts.Count -gt 0) {
    $args += @("--extra-web-ports", ($ExtraWebPorts -join ","))
}

& $node @args
exit $LASTEXITCODE
