from __future__ import annotations

import os
import sys
from pathlib import Path


def configure_safe_graphics() -> None:
    """Force a conservative rendering path for older Intel/Haswell systems."""
    if os.environ.get("ARCHYTER_HW_ACCEL", "0") == "1":
        return

    # Qt/Qt Quick: software rendering.
    os.environ.setdefault("QT_OPENGL", "software")
    os.environ.setdefault("QT_QUICK_BACKEND", "software")
    # Haswell is <= Gen 7.5. On Arch, VA-API should use i965 rather than iHD.
    os.environ.setdefault("LIBVA_DRIVER_NAME", "i965")

    # Chromium/QtWebEngine: do not start Vulkan, GPU compositing or VA-API.
    current_flags = os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "")
    safe_flags = " ".join(
        [
            "--disable-gpu",
            "--disable-gpu-compositing",
            "--disable-gpu-rasterization",
            "--disable-vulkan",
            "--disable-accelerated-video-decode",
            "--disable-accelerated-video-encode",
            "--disable-features=VaapiVideoDecoder,VaapiVideoEncoder,Vulkan",
            "--use-gl=disabled",
            "--log-level=3",
        ]
    )
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
        f"{current_flags} {safe_flags}".strip()
    )


# IMPORTANT: these variables must be set before importing any PySide6 module.
configure_safe_graphics()

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
    app.setStyle("Fusion")

    window = MainWindow(root_dir=resolve_root_dir())
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
