from __future__ import annotations

import os
import signal
import sys
from pathlib import Path

os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")

# Chromium can incorrectly classify an embedded QtWebEngine surface as
# occluded on Windows. The visible symptom is exactly what Archyter users
# reported: Jupyter appears stuck, then immediately advances after minimizing
# and restoring the window. Keep the renderer active while the IDE is visible.
if os.name == "nt":
    current_flags = os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "")
    required_flags = (
        "--disable-features=CalculateNativeWinOcclusion",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--disable-background-timer-throttling",
    )
    missing = [
        flag
        for flag in required_flags
        if flag not in current_flags
    ]
    if missing:
        os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = " ".join(
            part
            for part in (
                current_flags.strip(),
                *missing,
            )
            if part
        )

from PySide6.QtCore import QSettings, QTimer
from PySide6.QtWidgets import QApplication

from .icons import app_icon
from .window import StudioWindow


def resolve_project() -> str:
    if len(sys.argv) > 1:
        candidate = Path(sys.argv[1]).expanduser()
        if candidate.is_dir():
            return str(candidate.resolve())

    settings = QSettings("EduardoMedinaLabs", "ArchyterStudio")
    stored = settings.value("last_project", "")
    if stored and Path(str(stored)).is_dir():
        return str(Path(str(stored)).resolve())

    default = Path.home() / "Documents" / "Archyter Projects"
    default.mkdir(parents=True, exist_ok=True)
    return str(default)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Archyter Studio")
    app.setOrganizationName("EduardoMedinaLabs")
    app.setStyle("Fusion")
    app.setWindowIcon(app_icon())

    window = StudioWindow(resolve_project())
    window.show()

    timer = QTimer()
    timer.setInterval(250)
    timer.timeout.connect(lambda: None)
    timer.start()

    closing = False

    def shutdown(*_args) -> None:
        nonlocal closing
        if closing:
            return
        closing = True
        window.close()
        app.quit()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
