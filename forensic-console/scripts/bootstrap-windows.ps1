$ErrorActionPreference = "Stop"

Write-Host "== BlackArch Forensic Console bootstrap ==" -ForegroundColor Cyan

function Require-Command([string]$Name, [string]$Hint) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name is required. $Hint"
    }
}

Require-Command "node" "Install Node.js 20+."
Require-Command "npm" "Install npm with Node.js."
Require-Command "cargo" "Install Rust using rustup."
Require-Command "wsl.exe" "Enable WSL2 on Windows 11."

$distros = (& wsl.exe -l -q) -replace [char]0, ""
if (-not ($distros | Where-Object { $_.Trim().ToLower() -eq "archlinux" })) {
    Write-Warning "WSL distro 'archlinux' was not found. You can change the distro later in Settings."
}

Write-Host "Installing JavaScript dependencies..." -ForegroundColor Green
npm install

Write-Host "Running Rust core tests..." -ForegroundColor Green
cargo test -p forensic-core

Write-Host "Running frontend typecheck..." -ForegroundColor Green
npm run frontend:check

Write-Host ""
Write-Host "Ready. Start the desktop app with:" -ForegroundColor Cyan
Write-Host "  npm run dev"
