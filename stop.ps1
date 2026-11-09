param([switch]$DryRun)

# run.ps1 starts hidden PowerShell windows whose children (python, node) own the
# ports. Stopping the listeners lets each parent window exit on its own.
$listeners = Get-NetTCPConnection -LocalPort 8000, 5173 -State Listen -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique
if (-not $listeners) {
    Write-Host 'Doppelganger is not running.'
    exit 0
}
foreach ($id in $listeners) {
    if ($DryRun) {
        Write-Host "Stop-Process -Id $id"
    } else {
        Stop-Process -Id $id -Force -ErrorAction SilentlyContinue
        Write-Host "Stopped PID $id"
    }
}
