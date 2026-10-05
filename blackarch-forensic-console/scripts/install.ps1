param(
    [switch]$InstallToolchain,
    [switch]$NoShortcut
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

function Refresh-Path {
    $machine = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $user = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machine;$user"
}

if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
    throw "WSL no está disponible. Instala WSL2 primero."
}

$Distros = (wsl.exe -l -q) -join "`n"
if ($Distros -notmatch "archlinux") {
    Write-Warning "No encontré una distro llamada 'archlinux'."
}

if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
    if (-not $InstallToolchain) {
        throw "Rust no está instalado. Vuelve a ejecutar con -InstallToolchain."
    }
    if (-not (Get-Command winget.exe -ErrorAction SilentlyContinue)) {
        throw "winget no está disponible."
    }
    winget install --id Rustlang.Rustup --exact --accept-package-agreements --accept-source-agreements
    Refresh-Path
}

if ($InstallToolchain) {
    $vswhere = "$env:ProgramFiles(x86)\Microsoft Visual Studio\Installer\vswhere.exe"
    $hasVc = $false
    if (Test-Path $vswhere) {
        $vc = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
        $hasVc = -not [string]::IsNullOrWhiteSpace($vc)
    }
    if (-not $hasVc) {
        winget install --id Microsoft.VisualStudio.2022.BuildTools --exact --accept-package-agreements --accept-source-agreements --override "--wait --passive --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
    }
}

& (Join-Path $Root "scripts\build-windows.ps1")

$Exe = Join-Path $Root "dist\BlackArchForensicConsole.exe"
if (-not (Test-Path $Exe)) { throw "No se generó el ejecutable esperado: $Exe" }

if (-not $NoShortcut) {
    $Desktop = [Environment]::GetFolderPath("Desktop")
    $ShortcutPath = Join-Path $Desktop "BlackArch Forensic Console.lnk"
    $Shell = New-Object -ComObject WScript.Shell
    $Shortcut = $Shell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = $Exe
    $Shortcut.WorkingDirectory = Split-Path $Exe
    $Shortcut.IconLocation = "$Exe,0"
    $Shortcut.Description = "BlackArch WSL2 DFIR Workspace"
    $Shortcut.Save()
}

Write-Host "Instalación terminada: $Exe" -ForegroundColor Green
