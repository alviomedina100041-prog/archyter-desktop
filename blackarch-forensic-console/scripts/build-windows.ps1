param([switch]$Debug)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
    throw "cargo no está instalado. Ejecuta .\scripts\install.ps1 -InstallToolchain."
}

Write-Host "[1/3] Tests de lógica" -ForegroundColor Cyan
cargo test --lib

if ($Debug) {
    Write-Host "[2/3] Build debug" -ForegroundColor Cyan
    cargo build
    $Exe = Join-Path $Root "target\debug\blackarch-forensic-console.exe"
} else {
    Write-Host "[2/3] Build release optimizado" -ForegroundColor Cyan
    cargo build --release
    $Exe = Join-Path $Root "target\release\blackarch-forensic-console.exe"
}

Write-Host "[3/3] Preparando dist" -ForegroundColor Cyan
$Dist = Join-Path $Root "dist"
New-Item -ItemType Directory -Force -Path (Join-Path $Dist "assets") | Out-Null
Copy-Item $Exe (Join-Path $Dist "BlackArchForensicConsole.exe") -Force
Copy-Item (Join-Path $Root "assets\blackarch.ico") (Join-Path $Dist "assets\blackarch.ico") -Force

$Size = (Get-Item (Join-Path $Dist "BlackArchForensicConsole.exe")).Length / 1MB
Write-Host ("OK: dist\BlackArchForensicConsole.exe ({0:N2} MB)" -f $Size) -ForegroundColor Green
