param(
    [int]$Port = $(if ($env:TENDER_KILLER_BROWSER_CDP_PORT) { [int]$env:TENDER_KILLER_BROWSER_CDP_PORT } else { 9222 }),
    [string]$ProfileDir = $(Join-Path (Split-Path -Parent $PSScriptRoot) 'data\browser-bridge-profile'),
    [ValidateSet('auto', 'edge', 'chrome')]
    [string]$Browser = 'auto'
)

$ErrorActionPreference = 'Stop'

function Resolve-BrowserPath {
    $candidates = @()
    if ($Browser -in @('auto', 'edge')) {
        $candidates += @(
            "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
            "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe"
        )
    }
    if ($Browser -in @('auto', 'chrome')) {
        $candidates += @(
            "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
            "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe"
        )
    }
    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) {
            return $candidate
        }
    }
    throw 'Chrome or Edge was not found. Install a browser or pass -Browser chrome/edge.'
}

$browserPath = Resolve-BrowserPath
New-Item -Path $ProfileDir -ItemType Directory -Force | Out-Null

$args = @(
    "--remote-debugging-port=$Port",
    "--user-data-dir=$ProfileDir",
    '--no-first-run',
    '--no-default-browser-check',
    'https://www.vseinstrumenti.ru/'
)

Start-Process -FilePath $browserPath -ArgumentList $args -WindowStyle Normal

[pscustomobject]@{
    browser = $browserPath
    profile = (Resolve-Path -LiteralPath $ProfileDir).Path
    cdp_url = "http://127.0.0.1:$Port"
    env_hint = "`$env:TENDER_KILLER_BROWSER_CDP_URL='http://127.0.0.1:$Port'"
} | Format-List
