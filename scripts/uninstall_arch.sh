#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/archyter-desktop"
DESKTOP_FILE="${XDG_DATA_HOME:-$HOME/.local/share}/applications/archyter-desktop.desktop"
BIN_FILE="$HOME/.local/bin/archyter"

rm -rf "$INSTALL_DIR"
rm -f "$DESKTOP_FILE"
rm -f "$BIN_FILE"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${XDG_DATA_HOME:-$HOME/.local/share}/applications" || true
fi

echo "Archyter Desktop fue desinstalado de tu usuario."
