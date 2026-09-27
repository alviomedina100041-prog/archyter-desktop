#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/archyter-desktop"
DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
BIN_DIR="$HOME/.local/bin"
STAGING_DIR="${INSTALL_DIR}.new"

echo "== Archyter Desktop Installer =="
echo
echo "Origen:      $SOURCE_DIR"
echo "Instalación: $INSTALL_DIR"
echo

echo "[1/6] Dependencias de Arch Linux"
sudo pacman -S --needed \
  python \
  python-pip \
  python-virtualenv \
  mesa \
  libva \
  libva-intel-driver \
  libva-utils

echo "[2/6] Preparando instalación local"
rm -rf "$STAGING_DIR"
mkdir -p "$STAGING_DIR" "$DESKTOP_DIR" "$BIN_DIR"

cp -a "$SOURCE_DIR/app" "$STAGING_DIR/"
cp -a "$SOURCE_DIR/assets" "$STAGING_DIR/"
cp -a "$SOURCE_DIR/scripts" "$STAGING_DIR/"
cp "$SOURCE_DIR/requirements.txt" "$STAGING_DIR/"
cp "$SOURCE_DIR/README.md" "$STAGING_DIR/" 2>/dev/null || true

chmod +x "$STAGING_DIR/scripts/run_archyter.sh"
chmod +x "$STAGING_DIR/scripts/install_arch.sh"

echo "[3/6] Creando entorno privado"
python -m venv "$STAGING_DIR/.venv"
"$STAGING_DIR/.venv/bin/python" -m pip install --upgrade pip
"$STAGING_DIR/.venv/bin/python" -m pip install -r "$STAGING_DIR/requirements.txt"

echo "[4/6] Activando nueva versión"
rm -rf "$INSTALL_DIR"
mv "$STAGING_DIR" "$INSTALL_DIR"

echo "[5/6] Registrando aplicación de escritorio"
sed "s|__PROJECT_DIR__|$INSTALL_DIR|g" \
  "$INSTALL_DIR/scripts/archyter-desktop.desktop" \
  > "$DESKTOP_DIR/archyter-desktop.desktop"
chmod +x "$DESKTOP_DIR/archyter-desktop.desktop"

cat > "$BIN_DIR/archyter" <<EOF
#!/usr/bin/env bash
exec "$INSTALL_DIR/scripts/run_archyter.sh" "\$@"
EOF
chmod +x "$BIN_DIR/archyter"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$DESKTOP_DIR" || true
fi

echo "[6/6] Instalación terminada"
echo
echo "Archyter ya quedó instalado de forma permanente."
echo
echo "Puedes abrirlo desde el menú de aplicaciones:"
echo "  Archyter Desktop"
echo
echo "O desde cualquier terminal con:"
echo "  archyter"
echo
echo "La aplicación del menú usa Terminal=false, así que no abre una consola externa."
