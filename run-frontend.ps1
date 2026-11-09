param([switch]$DryRun)

$ErrorActionPreference = 'Stop'
$frontendRoot = Join-Path $PSScriptRoot 'frontend'
$npm = Get-Command npm -ErrorAction SilentlyContinue

if ($DryRun) {
    Write-Host "npm run dev (cwd: $frontendRoot, http://127.0.0.1:5173)"
    exit 0
}
if (-not $npm) {
    throw 'Node.js and npm were not found. Install Node.js 20+ and run .\setup.ps1 again.'
}
if (-not (Test-Path -LiteralPath (Join-Path $frontendRoot 'node_modules'))) {
    throw 'Frontend dependencies are missing. Run .\setup.ps1 first.'
}
Push-Location $frontendRoot
try {
    & $npm.Source run dev
} finally {
    Pop-Location
}
