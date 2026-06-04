$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
$apiBaseUrl = "http://127.0.0.1:8000"
$webBaseUrl = "http://127.0.0.1:5173"
$logsDir = Join-Path $root "logs"

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

Repair-ProcessPathEnvironment

if (-not (Test-Path $python)) {
    throw "Python venv not found: $python"
}
if (-not (Test-Path $logsDir)) {
    New-Item -Path $logsDir -ItemType Directory | Out-Null
}

$ocrWrapper = Join-Path $root "scripts\ocr-pdf.ps1"
if (-not $env:TENDER_KILLER_PDF_OCR_COMMAND -and (Test-Path -LiteralPath $ocrWrapper)) {
    $env:TENDER_KILLER_PDF_OCR_COMMAND = "powershell -NoProfile -ExecutionPolicy Bypass -File `"$ocrWrapper`" {path}"
}

function Find-BrowserFetchNode {
    if ($env:TENDER_KILLER_BROWSER_NODE_PATH -and (Test-Path -LiteralPath $env:TENDER_KILLER_BROWSER_NODE_PATH)) {
        return $env:TENDER_KILLER_BROWSER_NODE_PATH
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
    $node = (Get-Command node.exe -ErrorAction SilentlyContinue).Source
    if ($node) {
        return $node
    }
    return $null
}

if (-not $env:TENDER_KILLER_SUPPLIER_BROWSER_FETCH) {
    $env:TENDER_KILLER_SUPPLIER_BROWSER_FETCH = "1"
}
if (-not $env:TENDER_KILLER_SUPPLIER_BROWSER_FETCH_PROVIDERS) {
    $env:TENDER_KILLER_SUPPLIER_BROWSER_FETCH_PROVIDERS = "officemag"
}
if (-not $env:TENDER_KILLER_BROWSER_PROFILE_DIR) {
    $env:TENDER_KILLER_BROWSER_PROFILE_DIR = Join-Path $root "data\browser-profile\supplier-fetch"
}
if (-not $env:TENDER_KILLER_BROWSER_NODE_PATH) {
    $browserFetchNode = Find-BrowserFetchNode
    if ($browserFetchNode) {
        $env:TENDER_KILLER_BROWSER_NODE_PATH = $browserFetchNode
    }
}

function Find-Npm {
    $npm = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source
    if ($npm) {
        return $npm
    }
    $node = (Get-Command node.exe -ErrorAction SilentlyContinue).Source
    if ($node) {
        $candidate = Join-Path (Split-Path -Parent $node) "npm.cmd"
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }
    return $null
}

function Find-LocalViteScript {
    $viteScript = Join-Path $root "web\node_modules\vite\bin\vite.js"
    if (Test-Path -LiteralPath $viteScript) {
        return $viteScript
    }
    return $null
}

function Find-ViteNode {
    if ($env:TENDER_KILLER_VITE_NODE_PATH -and (Test-Path -LiteralPath $env:TENDER_KILLER_VITE_NODE_PATH)) {
        return $env:TENDER_KILLER_VITE_NODE_PATH
    }
    return Find-BrowserFetchNode
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

function Get-PortOwnerPid {
    param([int]$Port)
    try {
        $connection = Get-NetTCPConnection -LocalAddress "127.0.0.1" -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($connection) {
            return [int]$connection.OwningProcess
        }
    }
    catch {
        return $null
    }
    return $null
}

function Stop-StalePortProcess {
    param(
        [int]$Port,
        [string]$Reason
    )
    $ownerPid = Get-PortOwnerPid -Port $Port
    if (-not $ownerPid) {
        return
    }
    if ($Port -eq 8000) {
        Write-Host "Port 8000 is already in use by a stale or unhealthy API process. Restarting it. $Reason"
    }
    else {
        Write-Host "Port $Port is already in use by a stale or unhealthy dev process. Restarting it. $Reason"
    }
    Stop-Process -Id $ownerPid -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 700
}

function Test-ApiHealth {
    # dev_health verifies /api/health capabilities and /api/sources/status.
    & $python -m tender_killer.dev_health --base-url $apiBaseUrl --timeout 2 --quiet
    return $LASTEXITCODE -eq 0
}

function Test-WebHealth {
    try {
        $html = Invoke-WebRequest -Uri $webBaseUrl -UseBasicParsing -TimeoutSec 2
        if ($html.StatusCode -lt 200 -or $html.StatusCode -ge 300 -or -not $html.Content.Contains('id="root"')) {
            return $false
        }
        $health = Invoke-WebRequest -Uri "$webBaseUrl/api/health" -UseBasicParsing -TimeoutSec 2
        return $health.StatusCode -ge 200 -and $health.StatusCode -lt 300
    }
    catch {
        return $false
    }
}

function Start-ApiProcess {
    $apiArgs = @("-m", "tender_killer.web_api", "--host", "127.0.0.1", "--port", "8000")
    Start-Process `
        -FilePath $python `
        -ArgumentList $apiArgs `
        -WorkingDirectory $root `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logsDir "api-dev.out.log") `
        -RedirectStandardError (Join-Path $logsDir "api-dev.err.log") `
        -PassThru
}

function Start-StaticWebProcess {
    $distRoot = Join-Path $root "web\dist"
    if (-not (Test-Path -LiteralPath (Join-Path $distRoot "index.html"))) {
        throw "Static frontend build not found at $distRoot. Run web build once or install npm for Vite dev mode."
    }
    $webArgs = @(
        "-m", "tender_killer.dev_static_proxy",
        "--root", $distRoot,
        "--host", "127.0.0.1",
        "--port", "5173",
        "--api-base-url", $apiBaseUrl
    )
    Start-Process `
        -FilePath $python `
        -ArgumentList $webArgs `
        -WorkingDirectory $root `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logsDir "web-static.out.log") `
        -RedirectStandardError (Join-Path $logsDir "web-static.err.log") `
        -PassThru
}

function Start-ViteProcess {
    param([string]$NpmPath)
    Start-Process `
        -FilePath $NpmPath `
        -ArgumentList @("--prefix", (Join-Path $root "web"), "run", "dev") `
        -WorkingDirectory $root `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logsDir "web-vite.out.log") `
        -RedirectStandardError (Join-Path $logsDir "web-vite.err.log") `
        -PassThru
}

function Start-ViteNodeProcess {
    param(
        [string]$NodePath,
        [string]$ViteScript
    )
    Start-Process `
        -FilePath $NodePath `
        -ArgumentList @($ViteScript, "--host", "127.0.0.1", "--port", "5173") `
        -WorkingDirectory (Join-Path $root "web") `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logsDir "web-vite.out.log") `
        -RedirectStandardError (Join-Path $logsDir "web-vite.err.log") `
        -PassThru
}

function Restart-ManagedProcess {
    param(
        [System.Diagnostics.Process]$Process,
        [scriptblock]$Start
    )
    if ($Process -and -not $Process.HasExited) {
        Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 500
    }
    return & $Start
}

$npm = Find-Npm
$localViteScript = Find-LocalViteScript
$viteNode = if ($localViteScript) { Find-ViteNode } else { $null }
$forceStatic = $env:TENDER_KILLER_DEV_FORCE_STATIC -eq "1"
$webMode = if ($forceStatic -or (-not $npm -and -not ($localViteScript -and $viteNode))) { "static" } else { "vite" }
$apiProcess = $null
$webProcess = $null
$lastStatus = ""

Write-Host "Tender Killer dev supervisor"
Write-Host "- API: $apiBaseUrl"
Write-Host "- Web: $webBaseUrl"
Write-Host "- Web mode: $webMode"
if (-not $npm -and $localViteScript -and $viteNode -and -not $forceStatic) {
    Write-Host "- npm.cmd was not found; using local Vite script with Node: $viteNode"
}
elseif (-not $npm) {
    Write-Host "- npm.cmd and local Vite runtime were not found; using Python static proxy fallback."
}
Write-Host "- Press Ctrl+C to stop managed processes."

try {
    while ($true) {
        if (-not (Test-ApiHealth)) {
            if (Test-TcpPort -HostName "127.0.0.1" -Port 8000) {
                Stop-StalePortProcess -Port 8000 -Reason "API health check failed."
            }
            $apiProcess = Restart-ManagedProcess -Process $apiProcess -Start { Start-ApiProcess }
            $deadline = (Get-Date).AddSeconds(15)
            while ((Get-Date) -lt $deadline -and -not (Test-ApiHealth)) {
                Start-Sleep -Milliseconds 500
            }
            if (-not (Test-ApiHealth)) {
                Write-Host "Tender Killer API is still unhealthy; next supervisor tick will retry."
            }
        }

        if (-not (Test-WebHealth)) {
            if (Test-TcpPort -HostName "127.0.0.1" -Port 5173) {
                Stop-StalePortProcess -Port 5173 -Reason "Web health check failed."
            }
            if ($webMode -eq "vite") {
                if ($npm) {
                    $webProcess = Restart-ManagedProcess -Process $webProcess -Start { Start-ViteProcess -NpmPath $npm }
                }
                else {
                    $webProcess = Restart-ManagedProcess -Process $webProcess -Start { Start-ViteNodeProcess -NodePath $viteNode -ViteScript $localViteScript }
                }
                $deadline = (Get-Date).AddSeconds(10)
                while ((Get-Date) -lt $deadline -and -not (Test-WebHealth)) {
                    Start-Sleep -Milliseconds 500
                }
                if (-not (Test-WebHealth)) {
                    Write-Host "Vite did not become healthy; switching to Python static proxy fallback."
                    $webMode = "static"
                }
            }
            if ($webMode -eq "static" -and -not (Test-WebHealth)) {
                $webProcess = Restart-ManagedProcess -Process $webProcess -Start { Start-StaticWebProcess }
                $deadline = (Get-Date).AddSeconds(10)
                while ((Get-Date) -lt $deadline -and -not (Test-WebHealth)) {
                    Start-Sleep -Milliseconds 500
                }
            }
        }

        $status = "api=$((Test-ApiHealth).ToString().ToLower()) web=$((Test-WebHealth).ToString().ToLower()) mode=$webMode"
        if ($status -ne $lastStatus) {
            Write-Host "Tender Killer dev status: $status"
            $lastStatus = $status
        }
        Start-Sleep -Seconds 3
    }
}
finally {
    if ($apiProcess -and -not $apiProcess.HasExited) {
        Stop-Process -Id $apiProcess.Id -Force -ErrorAction SilentlyContinue
    }
    if ($webProcess -and -not $webProcess.HasExited) {
        Stop-Process -Id $webProcess.Id -Force -ErrorAction SilentlyContinue
    }
}
