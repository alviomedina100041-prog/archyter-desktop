#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "== Archyter Desktop =="
echo

echo "[1/4] Dependencias base de Arch Linux"
sudo pacman -S --needed python python-pip python-virtualenv

echo "[2/4] Entorno virtual"
python -m venv .venv
source .venv/bin/activate

echo "[3/4] Dependencias Python"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "[4/4] Launcher de escritorio"
mkdir -p "$HOME/.local/share/applications"
sed "s|__PROJECT_DIR__|$PROJECT_DIR|g" scripts/archyter-desktop.desktop \
  > "$HOME/.local/share/applications/archyter-desktop.desktop"
chmod +x "$HOME/.local/share/applications/archyter-desktop.desktop"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$HOME/.local/share/applications" || true
fi

echo
echo "Instalación terminada."
echo "Ejecuta ahora:"
echo "  source .venv/bin/activate"
echo "  python -m app.main"
echo
echo "También puedes buscar 'Archyter Desktop' en el menú de aplicaciones."
