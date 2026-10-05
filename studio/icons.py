from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QStyle


_ICON_DIR = Path(__file__).resolve().parent / "assets" / "icons"


def icon(name: str, fallback: QStyle.StandardPixmap | None = None) -> QIcon:
    path = _ICON_DIR / f"{name}.svg"
    if path.exists():
        candidate = QIcon(str(path))
        if not candidate.isNull():
            return candidate

    app = QApplication.instance()
    if app is not None and fallback is not None:
        return app.style().standardIcon(fallback)

    return QIcon()


def app_icon() -> QIcon:
    return icon("app", QStyle.StandardPixmap.SP_ComputerIcon)
