$ErrorActionPreference = "Stop"

$ProjectDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectDir

$Python = Join-Path $ProjectDir ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    Write-Error "No existe .venv. Ejecuta primero scripts\install_windows.ps1"
}

& $Python -m studio.main @args
