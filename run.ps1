param([switch]$DryRun)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$runtimeRoot = Join-Path (Split-Path $projectRoot -Parent) 'DoppelgangerRuntime'
$venvPython = Join-Path $runtimeRoot '.venv\Scripts\python.exe'
$env:HF_HOME = Join-Path $runtimeRoot '.cache\huggingface'

if ($DryRun) {
    Write-Host "$venvPython -m uvicorn thai_voice_clone.api:app --host 127.0.0.1 --port 8000 (http://127.0.0.1:8000)"
    Write-Host "npm run dev (cwd: $(Join-Path $projectRoot 'frontend'), http://127.0.0.1:5173)"
    exit 0
}
if (-not (Test-Path -LiteralPath $venvPython)) {
    throw 'The environment is missing. Run .\setup.ps1 first.'
}
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw 'Node.js and npm were not found. Install Node.js 20+ and run .\setup.ps1 again.'
}
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'frontend\node_modules'))) {
    throw 'Frontend dependencies are missing. Run .\setup.ps1 first.'
}
New-Item -ItemType Directory -Force -Path (Join-Path $projectRoot 'outputs\generated') | Out-Null
$logDir = Join-Path $projectRoot 'outputs\logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$backend = Start-Process -FilePath 'powershell.exe' -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logDir 'backend.log') -RedirectStandardError (Join-Path $logDir 'backend.error.log') -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $projectRoot 'run-backend.ps1'))
$frontend = Start-Process -FilePath 'powershell.exe' -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logDir 'frontend.log') -RedirectStandardError (Join-Path $logDir 'frontend.error.log') -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $projectRoot 'run-frontend.ps1'))
Write-Host "Backend started (PID $($backend.Id)): http://127.0.0.1:8000"
Write-Host "Frontend started (PID $($frontend.Id)): http://127.0.0.1:5173"
Write-Host "Logs: $logDir"
Start-Sleep -Seconds 2
Start-Process 'http://127.0.0.1:5173'
