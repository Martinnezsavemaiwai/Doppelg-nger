param([switch]$DryRun)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$runtimeRoot = Join-Path (Split-Path $projectRoot -Parent) 'DoppelgangerRuntime'
$venvPython = Join-Path $runtimeRoot '.venv\Scripts\python.exe'
$env:HF_HOME = Join-Path $runtimeRoot '.cache\huggingface'

if ($DryRun) {
    Write-Host "$venvPython -m uvicorn thai_voice_clone.api:app --host 127.0.0.1 --port 8000 (http://127.0.0.1:8000)"
    exit 0
}
if (-not (Test-Path -LiteralPath $venvPython)) {
    throw 'The environment is missing. Run .\setup.ps1 first.'
}
New-Item -ItemType Directory -Force -Path (Join-Path $projectRoot 'outputs\generated') | Out-Null
Push-Location $runtimeRoot
try {
    & $venvPython -m uvicorn thai_voice_clone.api:app --host 127.0.0.1 --port 8000
} finally {
    Pop-Location
}
