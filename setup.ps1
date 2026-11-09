param(
    [switch]$CheckOnly,
    [double]$MinimumFreeGB = 20
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$runtimeRoot = Join-Path (Split-Path $projectRoot -Parent) 'DoppelgangerRuntime'
$projectDrive = (Get-Item -LiteralPath $projectRoot).PSDrive
$freeGB = [math]::Round($projectDrive.Free / 1GB, 1)

Write-Host 'Doppelganger system check'
Write-Host "Free disk space: $freeGB GB (minimum: $MinimumFreeGB GB)"
if ($freeGB -lt $MinimumFreeGB) {
    throw "Not enough disk space. Free at least $MinimumFreeGB GB on drive $($projectDrive.Name):"
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    throw 'Python was not found. Install 64-bit Python 3.10-3.12.'
}
$pythonInfo = & $python.Source -c "import json,platform,sys; print(json.dumps({'version': list(sys.version_info[:3]), 'bits': platform.architecture()[0]}))" | ConvertFrom-Json
$minor = [int]$pythonInfo.version[1]
if ([int]$pythonInfo.version[0] -ne 3 -or $minor -lt 10 -or $minor -gt 12 -or $pythonInfo.bits -ne '64bit') {
    throw "Python must be 64-bit version 3.10-3.12 (found $($pythonInfo.version -join '.'))."
}
Write-Host "Python: $($pythonInfo.version -join '.') $($pythonInfo.bits)"

foreach ($tool in @('ffmpeg', 'ffprobe')) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        throw "$tool was not found. Install FFmpeg and add it to PATH."
    }
}
Write-Host 'FFmpeg: available'

$node = Get-Command node -ErrorAction SilentlyContinue
$npm = Get-Command npm -ErrorAction SilentlyContinue
if (-not $node -or -not $npm) {
    throw 'Node.js 20+ and npm were not found. Install Node.js and run setup again.'
}
Write-Host "Node.js: $(& $node.Source --version)"
Write-Host "npm: $(& $npm.Source --version)"

$nvidiaSmi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
if ($nvidiaSmi) {
    Write-Host 'NVIDIA GPU:'
    & $nvidiaSmi.Source --query-gpu=name,memory.total,driver_version --format=csv,noheader
    if ($LASTEXITCODE -ne 0) {
        Write-Warning 'nvidia-smi failed; CUDA will be checked again during installation.'
    }
} else {
    Write-Warning 'NVIDIA GPU not found. CPU synthesis will be much slower.'
}

if ($CheckOnly) {
    Write-Host 'System check passed. Nothing was installed.'
    exit 0
}

if (-not (Test-Path -LiteralPath $runtimeRoot)) {
    New-Item -ItemType Junction -Path $runtimeRoot -Target $projectRoot | Out-Null
}
$venvPython = Join-Path $runtimeRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $venvPython)) {
    & $python.Source -m venv (Join-Path $runtimeRoot '.venv')
}

$env:HF_HOME = Join-Path $runtimeRoot '.cache\huggingface'
& $venvPython -m pip install --upgrade 'pip==26.2.1' 'setuptools>=75' wheel
if ($LASTEXITCODE -ne 0) { throw 'Could not update Python packaging tools.' }
& $venvPython -m pip install 'torch==2.14.1+cu126' 'torchaudio==2.11.0+cu126' --index-url https://download.pytorch.org/whl/cu126
if ($LASTEXITCODE -ne 0) { throw 'Could not install the CUDA PyTorch packages.' }
& $venvPython -m pip install -e "$runtimeRoot[dev]"
if ($LASTEXITCODE -ne 0) { throw 'Could not install the project dependencies.' }
& $venvPython -c "import torch, gradio, soundfile, voxcpm; print('Synthesis device:', 'cuda' if torch.cuda.is_available() else 'cpu')"
if ($LASTEXITCODE -ne 0) { throw 'The installed synthesis environment failed its import check.' }
& $venvPython -c "import faster_whisper; print('Transcription backend: ready')"
if ($LASTEXITCODE -ne 0) { throw 'The installed transcription environment failed its import check.' }
$frontendRoot = Join-Path $projectRoot 'frontend'
if (Test-Path -LiteralPath (Join-Path $frontendRoot 'package-lock.json')) {
    & $npm.Source --prefix $frontendRoot ci
} else {
    & $npm.Source --prefix $frontendRoot install
}
if ($LASTEXITCODE -ne 0) { throw 'Could not install the frontend dependencies.' }
Write-Host 'Installation complete. Start with .\run.ps1'
