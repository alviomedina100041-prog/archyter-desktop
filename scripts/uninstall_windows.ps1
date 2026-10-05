$ErrorActionPreference = "Stop"
$InstallDir = Join-Path $env:LOCALAPPDATA "ArchyterStudio"
$Shortcut = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Archyter Studio.lnk"

if (Test-Path $Shortcut) { Remove-Item $Shortcut -Force }
if (Test-Path $InstallDir) { Remove-Item $InstallDir -Recurse -Force }

Write-Host "Archyter Studio fue desinstalado de este usuario." -ForegroundColor Green
