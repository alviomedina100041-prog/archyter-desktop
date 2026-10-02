from __future__ import annotations

import os
import signal
import sys
from pathlib import Path


def configure_safe_graphics() -> None:
    """Force a conservative rendering path for older Intel/Haswell systems."""
    if os.environ.get("ARCHYTER_HW_ACCEL", "0") == "1":
        return

    os.environ.setdefault("QT_OPENGL", "software")
    os.environ.setdefault("QT_QUICK_BACKEND", "software")
    os.environ.setdefault("LIBVA_DRIVER_NAME", "i965")

    fonts_conf = Path("/etc/fonts/fonts.conf")
    if fonts_conf.exists():
        os.environ.setdefault("FONTCONFIG_FILE", str(fonts_conf))
        os.environ.setdefault("FONTCONFIG_PATH", str(fonts_conf.parent))

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


configure_safe_graphics()

from PySide6.QtCore import QSettings, QTimer
from PySide6.QtWidgets import QApplication

from .icons import app_icon
from .window import MainWindow


def resolve_root_dir() -> str:
    if len(sys.argv) > 1:
        return os.path.abspath(os.path.expanduser(sys.argv[1]))

    env_root = os.environ.get("ARCHYTER_PROJECT")
    if env_root:
        return os.path.abspath(os.path.expanduser(env_root))

    settings = QSettings("EduardoMedinaLabs", "ArchyterDesktop")
    stored = settings.value("last_project", "")
    if stored:
        path = Path(str(stored)).expanduser()
        if path.is_dir():
            return str(path.resolve())

    return str(Path.home())


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Archyter Desktop")
    app.setOrganizationName("EduardoMedinaLabs")
    app.setDesktopFileName("archyter-desktop")
    app.setStyle("Fusion")
    app.setWindowIcon(app_icon())

    window = MainWindow(root_dir=resolve_root_dir())

    # Give Python regular interpreter time so Ctrl+C can perform a clean
    # shutdown of Jupyter and child shells instead of abruptly killing Qt.
    signal_timer = QTimer()
    signal_timer.setInterval(200)
    signal_timer.timeout.connect(lambda: None)
    signal_timer.start()

    closing = False

    def graceful_quit(*_args) -> None:
        nonlocal closing
        if closing:
            return
        closing = True
        window.close()
        app.quit()

    signal.signal(signal.SIGINT, graceful_quit)
    signal.signal(signal.SIGTERM, graceful_quit)

    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
