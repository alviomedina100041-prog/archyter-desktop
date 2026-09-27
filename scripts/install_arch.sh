#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "== Archyter Desktop =="
echo

echo "[1/5] Dependencias base de Arch Linux"
sudo pacman -S --needed \
  python \
  python-pip \
  python-virtualenv \
  mesa \
  libva \
  libva-intel-driver \
  libva-utils

echo "[2/5] Entorno virtual"
python -m venv .venv
source .venv/bin/activate

echo "[3/5] Dependencias Python"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "[4/5] Permisos del launcher"
chmod +x scripts/run_archyter.sh

echo "[5/5] Launcher de escritorio"
mkdir -p "$HOME/.local/share/applications"
sed "s|__PROJECT_DIR__|$PROJECT_DIR|g" scripts/archyter-desktop.desktop \
  > "$HOME/.local/share/applications/archyter-desktop.desktop"
chmod +x "$HOME/.local/share/applications/archyter-desktop.desktop"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$HOME/.local/share/applications" || true
fi

echo
echo "Instalación terminada."
echo
echo "Haswell detectado/compatible:"
echo "  Archyter fuerza renderizado por software."
echo "  VA-API usa i965 en lugar de iHD."
echo
echo "Para comprobar VA-API:"
echo "  LIBVA_DRIVER_NAME=i965 vainfo"
echo
echo "Ejecuta:"
echo "  ./scripts/run_archyter.sh"
echo
echo "También puedes buscar 'Archyter Desktop' en el menú de aplicaciones."
