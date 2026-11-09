param([switch]$DryRun)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$runtimeRoot = Join-Path (Split-Path $projectRoot -Parent) 'DoppelgangerRuntime'
$venvPython = Join-Path $runtimeRoot '.venv\Scripts\python.exe'
$env:HF_HOME = Join-Path $runtimeRoot '.cache\huggingface'

if ($DryRun) {
    Write-Host "$venvPython -m thai_voice_clone.app (http://127.0.0.1:7860)"
    exit 0
}
if (-not (Test-Path -LiteralPath $venvPython)) {
    throw 'The environment is missing. Run .\setup.ps1 first.'
}
New-Item -ItemType Directory -Force -Path (Join-Path $projectRoot 'outputs\generated') | Out-Null
Push-Location $runtimeRoot
try {
    & $venvPython -m thai_voice_clone.app
} finally {
    Pop-Location
}
