#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

if [[ ! -x ".venv/bin/python" ]]; then
    echo "Archyter: no existe .venv. Ejecuta primero scripts/install_arch.sh" >&2
    exit 1
fi

# Conservative path for Intel Haswell / older Intel graphics.
export QT_OPENGL=software
export QT_QUICK_BACKEND=software
export LIBVA_DRIVER_NAME=i965

EXTRA_FLAGS="--disable-gpu --disable-gpu-compositing --disable-gpu-rasterization --disable-vulkan --disable-accelerated-video-decode --disable-accelerated-video-encode --disable-features=VaapiVideoDecoder,VaapiVideoEncoder,Vulkan --use-gl=disabled --log-level=3"
export QTWEBENGINE_CHROMIUM_FLAGS="${QTWEBENGINE_CHROMIUM_FLAGS:-} ${EXTRA_FLAGS}"

TARGET="${1:-$HOME}"
exec .venv/bin/python -m app.main "$TARGET"
