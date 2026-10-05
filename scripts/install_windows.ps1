$ErrorActionPreference = "Stop"

$SourceDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$InstallDir = Join-Path $env:LOCALAPPDATA "ArchyterStudio"
$StartMenu = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
$ShortcutPath = Join-Path $StartMenu "Archyter Studio.lnk"

Write-Host "== Archyter Studio Installer ==" -ForegroundColor Cyan
Write-Host "Origen: $SourceDir"
Write-Host "Destino: $InstallDir"

$PythonCommand = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonCommand = @("py", "-3")
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonCommand = @("python")
} else {
    throw "Python 3 no está instalado. Instala Python 3.11+ y vuelve a ejecutar este instalador."
}

$Staging = "$InstallDir.new"
if (Test-Path $Staging) { Remove-Item $Staging -Recurse -Force }
New-Item -ItemType Directory -Force -Path $Staging | Out-Null

Copy-Item (Join-Path $SourceDir "studio") $Staging -Recurse
Copy-Item (Join-Path $SourceDir "assets") $Staging -Recurse
Copy-Item (Join-Path $SourceDir "scripts") $Staging -Recurse
Copy-Item (Join-Path $SourceDir "requirements-windows.txt") $Staging
Copy-Item (Join-Path $SourceDir "README.md") $Staging -ErrorAction SilentlyContinue

Push-Location $Staging
try {
    if ($PythonCommand[0] -eq "py") {
        & py -3 -m venv .venv
    } else {
        & python -m venv .venv
    }

    $VenvPython = Join-Path $Staging ".venv\Scripts\python.exe"
    & $VenvPython -m pip install --upgrade pip
    & $VenvPython -m pip install -r requirements-windows.txt

    $IconSvg = Join-Path $Staging "assets\icon.svg"
    $IconIco = Join-Path $Staging "ArchyterStudio.ico"
    & $VenvPython (Join-Path $Staging "scripts\build_windows_icon.py") $IconSvg $IconIco
} finally {
    Pop-Location
}

if (Test-Path $InstallDir) { Remove-Item $InstallDir -Recurse -Force }
Move-Item $Staging $InstallDir

$Launcher = Join-Path $InstallDir "ArchyterStudio.cmd"
@"
@echo off
cd /d "$InstallDir"
"$InstallDir\.venv\Scripts\python.exe" -m studio.main %*
"@ | Set-Content -Encoding ASCII $Launcher

$Pythonw = Join-Path $InstallDir ".venv\Scripts\pythonw.exe"
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $Pythonw
$Shortcut.Arguments = "-m studio.main"
$Shortcut.WorkingDirectory = $InstallDir
$Shortcut.Description = "Archyter Studio - Jupyter Desktop IDE"
$Shortcut.WindowStyle = 1
$Shortcut.IconLocation = "$InstallDir\ArchyterStudio.ico,0"
$Shortcut.Save()

Write-Host ""
Write-Host "Archyter Studio quedó instalado." -ForegroundColor Green
Write-Host "Búscalo en Inicio como: Archyter Studio"
Write-Host "Instalación: $InstallDir"
