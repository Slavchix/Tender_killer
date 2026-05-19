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
$api = Start-Process -FilePath $python -ArgumentList $apiArgs -WorkingDirectory $root -PassThru -WindowStyle Hidden

try {
    & $npm --prefix (Join-Path $root "web") run dev
}
finally {
    if ($api -and -not $api.HasExited) {
        Stop-Process -Id $api.Id -Force
    }
}
