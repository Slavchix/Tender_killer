param(
    [int]$ApiPort = $(if ($env:TENDER_KILLER_API_PORT) { [int]$env:TENDER_KILLER_API_PORT } else { 8000 }),
    [int]$WebPort = $(if ($env:TENDER_KILLER_WEB_PORT) { [int]$env:TENDER_KILLER_WEB_PORT } else { 5175 }),
    [int]$TimeoutSeconds = 12,
    [int[]]$ExtraWebPorts = @(5173, 5174)
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
$viteScript = Join-Path $root "web\node_modules\vite\bin\vite.js"
$logsDir = Join-Path $root "logs"
$runId = Get-Date -Format "yyyyMMdd-HHmmss"
$apiBaseUrl = "http://127.0.0.1:$ApiPort"
$webBaseUrl = "http://127.0.0.1:$WebPort"

function Repair-ProcessPathEnvironment {
    $cleanPath = [Environment]::GetEnvironmentVariable("Path", "Process")
    if (-not $cleanPath) {
        $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
        $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
        $cleanPath = @($userPath, $machinePath) -join ";"
    }
    [Environment]::SetEnvironmentVariable("PATH", $null, "Process")
    [Environment]::SetEnvironmentVariable("Path", $cleanPath, "Process")
}

function Find-Node {
    if ($env:TENDER_KILLER_VITE_NODE_PATH -and (Test-Path -LiteralPath $env:TENDER_KILLER_VITE_NODE_PATH)) {
        return $env:TENDER_KILLER_VITE_NODE_PATH
    }
    $node = (Get-Command node.exe -ErrorAction SilentlyContinue).Source
    if ($node) {
        return $node
    }
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
    return $null
}

function Get-PortOwnerPids {
    param([int]$Port)
    try {
        return @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
            Select-Object -ExpandProperty OwningProcess -Unique |
            Where-Object { $_ -and $_ -ne $PID })
    }
    catch {
        return @()
    }
}

function Stop-PortOwners {
    param([int]$Port)
    foreach ($ownerPid in Get-PortOwnerPids -Port $Port) {
        Write-Host "Stopping process $ownerPid on port $Port"
        Stop-Process -Id $ownerPid -Force -ErrorAction SilentlyContinue
    }
}

function Test-TcpPort {
    param(
        [string]$HostName,
        [int]$Port
    )
    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $connect = $client.BeginConnect($HostName, $Port, $null, $null)
        if (-not $connect.AsyncWaitHandle.WaitOne(300)) {
            return $false
        }
        $client.EndConnect($connect)
        return $true
    }
    catch {
        return $false
    }
    finally {
        $client.Close()
    }
}

function Test-HttpOk {
    param([string]$Url)
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
        return $response.StatusCode -ge 200 -and $response.StatusCode -lt 300
    }
    catch {
        return $false
    }
}

Repair-ProcessPathEnvironment

if (-not (Test-Path -LiteralPath $python)) {
    throw "Python venv not found: $python"
}
if (-not (Test-Path -LiteralPath $viteScript)) {
    throw "Vite script not found: $viteScript"
}
if (-not (Test-Path -LiteralPath $logsDir)) {
    New-Item -Path $logsDir -ItemType Directory | Out-Null
}

$node = Find-Node
if (-not $node) {
    throw "node.exe not found"
}

$ocrWrapper = Join-Path $root "scripts\ocr-pdf.ps1"
if (Test-Path -LiteralPath $ocrWrapper) {
    $env:TENDER_KILLER_PDF_OCR_COMMAND = "powershell -NoProfile -ExecutionPolicy Bypass -File `"$ocrWrapper`" {path}"
}
$env:TENDER_KILLER_SUPPLIER_BROWSER_FETCH = "1"
$env:TENDER_KILLER_SUPPLIER_BROWSER_FETCH_PROVIDERS = "officemag"
$env:TENDER_KILLER_BROWSER_NODE_PATH = $node

$portsToStop = @($ApiPort, $WebPort) + $ExtraWebPorts
$portsToStop | Select-Object -Unique | ForEach-Object { Stop-PortOwners -Port $_ }
Start-Sleep -Milliseconds 500

$apiOut = Join-Path $logsDir "api-dev-$ApiPort-$runId.out.log"
$apiErr = Join-Path $logsDir "api-dev-$ApiPort-$runId.err.log"
$webOut = Join-Path $logsDir "web-vite-$WebPort-$runId.out.log"
$webErr = Join-Path $logsDir "web-vite-$WebPort-$runId.err.log"

$apiProcess = Start-Process `
    -FilePath $python `
    -ArgumentList @("-m", "tender_killer.web_api", "--host", "127.0.0.1", "--port", "$ApiPort") `
    -WorkingDirectory $root `
    -WindowStyle Hidden `
    -RedirectStandardOutput $apiOut `
    -RedirectStandardError $apiErr `
    -PassThru

$webProcess = Start-Process `
    -FilePath $node `
    -ArgumentList @($viteScript, "--host", "127.0.0.1", "--port", "$WebPort") `
    -WorkingDirectory (Join-Path $root "web") `
    -WindowStyle Hidden `
    -RedirectStandardOutput $webOut `
    -RedirectStandardError $webErr `
    -PassThru

$apiReady = $false
$webReady = $false
$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
while ((Get-Date) -lt $deadline -and -not ($apiReady -and $webReady)) {
    if (-not $apiReady) {
        $apiReady = (Test-TcpPort -HostName "127.0.0.1" -Port $ApiPort) -and (Test-HttpOk -Url "$apiBaseUrl/api/health")
    }
    if (-not $webReady) {
        $webReady = (Test-TcpPort -HostName "127.0.0.1" -Port $WebPort) -and (Test-HttpOk -Url $webBaseUrl)
    }
    if (-not ($apiReady -and $webReady)) {
        Start-Sleep -Milliseconds 500
    }
}

[pscustomobject]@{
    api_pid = $apiProcess.Id
    web_pid = $webProcess.Id
    api_ready = $apiReady
    web_ready = $webReady
    api = $apiBaseUrl
    frontend = $webBaseUrl
    api_log = $apiErr
    web_log = $webErr
} | Format-List

if (-not ($apiReady -and $webReady)) {
    exit 1
}
