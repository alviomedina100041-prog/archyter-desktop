param([switch]$Debug)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
    throw "cargo no está instalado. Ejecuta .\scripts\install.ps1 -InstallToolchain."
}

cargo fmt --all -- --check
cargo test --lib

if ($Debug) {
    cargo build
    $Exe = Join-Path $Root "target\debug\blackarch-forensic-console.exe"
} else {
    cargo build --release
    $Exe = Join-Path $Root "target\release\blackarch-forensic-console.exe"
}

$Dist = Join-Path $Root "dist"
New-Item -ItemType Directory -Force -Path (Join-Path $Dist "assets") | Out-Null
Copy-Item $Exe (Join-Path $Dist "BlackArchForensicConsole.exe") -Force
Copy-Item (Join-Path $Root "assets\blackarch.ico") (Join-Path $Dist "assets\blackarch.ico") -Force
Copy-Item (Join-Path $Root "assets\blackarch.png") (Join-Path $Dist "assets\blackarch.png") -Force

$Size = (Get-Item (Join-Path $Dist "BlackArchForensicConsole.exe")).Length / 1MB
Write-Host ("OK: dist\BlackArchForensicConsole.exe ({0:N2} MB)" -f $Size) -ForegroundColor Green
