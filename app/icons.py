from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QStyle


def themed_icon(
    name: str,
    fallback: QStyle.StandardPixmap = QStyle.StandardPixmap.SP_FileIcon,
) -> QIcon:
    icon = QIcon.fromTheme(name)
    if not icon.isNull():
        return icon

    app = QApplication.instance()
    if app is not None:
        return app.style().standardIcon(fallback)

    return QIcon()


def app_icon() -> QIcon:
    for name in (
        "distributor-logo-archlinux",
        "archlinux",
        "start-here-archlinux",
    ):
        icon = QIcon.fromTheme(name)
        if not icon.isNull():
            return icon

    asset = Path(__file__).resolve().parent.parent / "assets" / "icon.svg"
    return QIcon(str(asset)) if asset.exists() else QIcon()
