from __future__ import annotations

import os
import sys
from pathlib import Path

# Archyter targets old Intel laptops too. QtWebEngine/Chromium may otherwise
# try Vulkan and VA-API paths that are noisy or unstable on Haswell.
if os.environ.get("ARCHYTER_HW_ACCEL", "0") != "1":
    current_flags = os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "")
    safe_flags = (
        "--disable-gpu "
        "--disable-vulkan "
        "--disable-features=VaapiVideoDecoder,VaapiVideoEncoder"
    )
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = f"{current_flags} {safe_flags}".strip()

from PySide6.QtWidgets import QApplication

from .window import MainWindow


def resolve_root_dir() -> str:
    if len(sys.argv) > 1:
        return os.path.abspath(os.path.expanduser(sys.argv[1]))

    env_root = os.environ.get("ARCHYTER_PROJECT")
    if env_root:
        return os.path.abspath(os.path.expanduser(env_root))

    return str(Path.home())


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Archyter Desktop")
    app.setOrganizationName("EduardoMedinaLabs")

    window = MainWindow(root_dir=resolve_root_dir())
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
