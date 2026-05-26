$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
$npm = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source
if (-not $npm) {
    $node = (Get-Command node.exe -ErrorAction SilentlyContinue).Source
    if ($node) {
        $candidate = Join-Path (Split-Path -Parent $node) "npm.cmd"
        if (Test-Path $candidate) {
            $npm = $candidate
        }
    }
}

if (-not (Test-Path $python)) {
    throw "Python venv not found: $python"
}
if (-not $npm) {
    throw "npm.cmd not found. Add portable Node.js folder to PATH before running npm run dev."
}

$apiArgs = @("-m", "tender_killer.web_api", "--host", "127.0.0.1", "--port", "8000")
$apiBaseUrl = "http://127.0.0.1:8000"

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

function Test-ApiHealth {
    # dev_health verifies /api/health capabilities and /api/sources/status.
    & $python -m tender_killer.dev_health --base-url $apiBaseUrl --timeout 2 --quiet
    return $LASTEXITCODE -eq 0
}

$api = $null
$startedApi = $false

if (Test-ApiHealth) {
    Write-Host "Tender Killer API already healthy at $apiBaseUrl"
}
elseif (Test-TcpPort -HostName "127.0.0.1" -Port 8000) {
    & $python -m tender_killer.dev_health --base-url $apiBaseUrl --timeout 2
    throw "Port 8000 is already in use by a non-compatible API. Stop the stale backend process and rerun npm run dev."
}
else {
    $api = Start-Process -FilePath $python -ArgumentList $apiArgs -WorkingDirectory $root -PassThru -WindowStyle Hidden
    $startedApi = $true
    $deadline = (Get-Date).AddSeconds(12)
    while ((Get-Date) -lt $deadline) {
        if (Test-ApiHealth) {
            break
        }
        Start-Sleep -Milliseconds 400
    }
    if (-not (Test-ApiHealth)) {
        if ($api -and -not $api.HasExited) {
            Stop-Process -Id $api.Id -Force
        }
        & $python -m tender_killer.dev_health --base-url $apiBaseUrl --timeout 2
        throw "Tender Killer API did not become healthy at $apiBaseUrl."
    }
}

try {
    & $npm --prefix (Join-Path $root "web") run dev
}
finally {
    if ($startedApi -and $api -and -not $api.HasExited) {
        Stop-Process -Id $api.Id -Force
    }
}
