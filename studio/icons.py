from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QIcon,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPolygonF,
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication, QStyle


SIZE = 64
ASSET_ROOT = Path(__file__).resolve().parents[1] / "assets"
ASSET_ICONS = {
    "app": "icon.svg",
    "python": "python-logo.svg",
}



@lru_cache(maxsize=24)
def asset_pixmap(name: str, size: int = 64) -> QPixmap:
    asset_name = ASSET_ICONS.get(name)
    if not asset_name:
        return QPixmap()

    asset_path = ASSET_ROOT / asset_name
    if not asset_path.is_file():
        return QPixmap()

    renderer = QSvgRenderer(str(asset_path))
    if not renderer.isValid():
        return QPixmap()

    pixel_size = max(16, int(size))
    pixmap = QPixmap(pixel_size, pixel_size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(
        QPainter.RenderHint.Antialiasing,
        True,
    )
    renderer.render(
        painter,
        QRectF(
            0,
            0,
            pixel_size,
            pixel_size,
        ),
    )
    painter.end()
    return pixmap


@lru_cache(maxsize=24)
def asset_icon(name: str) -> QIcon:
    pixmap = asset_pixmap(name, 256)
    if pixmap.isNull():
        return QIcon()

    result = QIcon()
    for size in (16, 20, 24, 32, 48, 64, 128, 256):
        scaled = pixmap.scaled(
            QSize(size, size),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        result.addPixmap(scaled)
    return result


def _pen(color: str, width: float = 4.0) -> QPen:
    pen = QPen(QColor(color))
    pen.setWidthF(width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return pen


def _pixmap() -> tuple[QPixmap, QPainter]:
    pixmap = QPixmap(SIZE, SIZE)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    return pixmap, painter


def _draw_app(p: QPainter) -> None:
    path = QPainterPath()
    path.moveTo(32, 5)
    path.lineTo(7, 57)
    path.lineTo(20, 57)
    path.lineTo(27, 41)
    path.lineTo(42, 41)
    path.lineTo(49, 57)
    path.lineTo(62, 57)
    path.closeSubpath()
    p.fillPath(path, QBrush(QColor("#179fe6")))

    inner = QPainterPath()
    inner.moveTo(32, 20)
    inner.lineTo(25, 36)
    inner.lineTo(39, 36)
    inner.closeSubpath()
    p.fillPath(inner, QBrush(QColor("#ffffff")))

    p.setPen(_pen("#0c72c4", 4.2))
    p.drawLine(QPointF(24, 48), QPointF(46, 48))


def _draw_folder(p: QPainter) -> None:
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor("#2f8ef0"))
    p.drawRoundedRect(QRectF(8, 16, 26, 13), 4, 4)
    p.setBrush(QColor("#58a9f6"))
    p.drawRoundedRect(QRectF(7, 23, 50, 31), 5, 5)
    p.setBrush(QColor("#8cc8fb"))
    p.drawRoundedRect(QRectF(10, 27, 44, 23), 4, 4)


def _draw_notebook(p: QPainter) -> None:
    p.setPen(_pen("#2187df", 3.2))
    p.setBrush(QColor("#ffffff"))
    p.drawRoundedRect(QRectF(13, 7, 40, 50), 5, 5)
    p.drawLine(QPointF(23, 8), QPointF(23, 56))
    p.setPen(_pen("#2187df", 2.8))
    for y in (20, 30, 40):
        p.drawLine(QPointF(30, y), QPointF(46, y))
    p.setBrush(QColor("#2187df"))
    p.setPen(Qt.PenStyle.NoPen)
    for y in (18, 31, 44):
        p.drawEllipse(QPointF(18, y), 2.2, 2.2)


def _draw_file(p: QPainter) -> None:
    path = QPainterPath()
    path.moveTo(16, 7)
    path.lineTo(39, 7)
    path.lineTo(51, 19)
    path.lineTo(51, 56)
    path.lineTo(16, 56)
    path.closeSubpath()
    p.setPen(_pen("#9aa9b9", 2.8))
    p.setBrush(QColor("#ffffff"))
    p.drawPath(path)
    p.drawLine(QPointF(39, 8), QPointF(39, 20))
    p.drawLine(QPointF(39, 20), QPointF(50, 20))


def _draw_python(p: QPainter) -> None:
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor("#3776ab"))
    p.drawRoundedRect(QRectF(10, 8, 33, 25), 9, 9)
    p.setBrush(QColor("#ffd343"))
    p.drawRoundedRect(QRectF(21, 31, 33, 25), 9, 9)
    p.setBrush(QColor("#ffffff"))
    p.drawEllipse(QPointF(32, 16), 2.3, 2.3)
    p.drawEllipse(QPointF(32, 48), 2.3, 2.3)


def _draw_add(p: QPainter) -> None:
    p.setPen(_pen("#176fc1", 5.0))
    p.drawLine(QPointF(32, 13), QPointF(32, 51))
    p.drawLine(QPointF(13, 32), QPointF(51, 32))


def _draw_trash(p: QPainter) -> None:
    p.setPen(_pen("#b43a45", 3.2))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawLine(QPointF(15, 20), QPointF(49, 20))
    p.drawRoundedRect(QRectF(20, 21, 24, 34), 3, 3)
    p.drawLine(QPointF(25, 14), QPointF(39, 14))
    p.drawLine(QPointF(29, 10), QPointF(35, 10))
    p.drawLine(QPointF(27, 29), QPointF(29, 47))
    p.drawLine(QPointF(37, 29), QPointF(35, 47))


def _draw_save(p: QPainter) -> None:
    p.setPen(_pen("#397ac3", 2.8))
    p.setBrush(QColor("#eaf4ff"))
    p.drawRoundedRect(QRectF(12, 9, 40, 46), 4, 4)
    p.setBrush(QColor("#397ac3"))
    p.drawRect(QRectF(20, 9, 24, 16))
    p.setBrush(QColor("#ffffff"))
    p.drawRoundedRect(QRectF(20, 34, 24, 15), 2, 2)


def _draw_play(p: QPainter, color: str = "#ffffff") -> None:
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(color))
    poly = QPolygonF([QPointF(20, 12), QPointF(51, 32), QPointF(20, 52)])
    p.drawPolygon(poly)


def _draw_run(p: QPainter) -> None:
    _draw_play(p, "#34506f")


def _draw_refresh(p: QPainter) -> None:
    p.setPen(_pen("#2c78c8", 4.0))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawArc(QRectF(10, 10, 44, 44), 35 * 16, 285 * 16)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor("#2c78c8"))
    p.drawPolygon(QPolygonF([QPointF(48, 8), QPointF(56, 20), QPointF(42, 20)]))


def _draw_terminal(p: QPainter) -> None:
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor("#1d2938"))
    p.drawRoundedRect(QRectF(7, 11, 50, 42), 6, 6)
    p.setPen(_pen("#ffffff", 3.2))
    p.drawLine(QPointF(16, 23), QPointF(24, 31))
    p.drawLine(QPointF(24, 31), QPointF(16, 39))
    p.drawLine(QPointF(30, 40), QPointF(44, 40))


def _draw_project(p: QPainter) -> None:
    _draw_folder(p)
    p.setPen(_pen("#ffffff", 2.6))
    p.drawLine(QPointF(16, 39), QPointF(47, 39))


def _draw_search(p: QPainter) -> None:
    p.setPen(_pen("#26384d", 4.0))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(QRectF(12, 10, 31, 31))
    p.drawLine(QPointF(39, 39), QPointF(53, 53))


def _draw_settings(p: QPainter) -> None:
    p.setPen(_pen("#26384d", 3.5))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(QRectF(23, 23, 18, 18))
    for angle in range(0, 360, 45):
        import math
        a = math.radians(angle)
        inner = QPointF(32 + 16 * math.cos(a), 32 + 16 * math.sin(a))
        outer = QPointF(32 + 23 * math.cos(a), 32 + 23 * math.sin(a))
        p.drawLine(inner, outer)


def _draw_home(p: QPainter) -> None:
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor("#277fda"))
    p.drawPolygon(QPolygonF([QPointF(8, 29), QPointF(32, 9), QPointF(56, 29)]))
    p.drawRoundedRect(QRectF(15, 27, 34, 29), 4, 4)
    p.setBrush(QColor("#ffffff"))
    p.drawRoundedRect(QRectF(27, 39, 10, 17), 2, 2)


def _draw_git(p: QPainter) -> None:
    p.setPen(_pen("#3d5068", 3.5))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawLine(QPointF(20, 13), QPointF(20, 45))
    p.drawLine(QPointF(20, 26), QPointF(43, 26))
    p.drawLine(QPointF(43, 26), QPointF(43, 42))
    p.setBrush(QColor("#ffffff"))
    for point in (QPointF(20, 13), QPointF(20, 49), QPointF(43, 47)):
        p.drawEllipse(point, 5.5, 5.5)


def _draw_grid(p: QPainter) -> None:
    p.setPen(_pen("#3d5068", 3.0))
    p.setBrush(Qt.BrushStyle.NoBrush)
    for x in (11, 36):
        for y in (11, 36):
            p.drawRoundedRect(QRectF(x, y, 17, 17), 3, 3)


def _draw_variables(p: QPainter) -> None:
    p.setPen(_pen("#31465d", 2.8))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(QRectF(9, 10, 46, 44), 5, 5)
    for y, width in ((21, 30), (32, 30), (43, 20)):
        p.drawLine(QPointF(17, y), QPointF(17 + width, y))


def _draw_stop(p: QPainter) -> None:
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor("#43536b"))
    p.drawRoundedRect(QRectF(18, 18, 28, 28), 4, 4)


def _draw_edit(p: QPainter) -> None:
    p.setPen(_pen("#3d6f9f", 3.3))
    p.setBrush(QColor("#eaf4ff"))
    p.drawRoundedRect(QRectF(12, 42, 31, 9), 3, 3)
    p.setBrush(QColor("#3d6f9f"))
    path = QPainterPath()
    path.moveTo(17, 39)
    path.lineTo(39, 17)
    path.lineTo(48, 26)
    path.lineTo(26, 48)
    path.lineTo(15, 50)
    path.closeSubpath()
    p.drawPath(path)
    p.setBrush(QColor("#ffffff"))
    p.drawPolygon(
        QPolygonF([
            QPointF(39, 17),
            QPointF(44, 12),
            QPointF(53, 21),
            QPointF(48, 26),
        ])
    )


def _draw_more(p: QPainter) -> None:
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor("#3b4b61"))
    for x in (20, 32, 44):
        p.drawEllipse(QPointF(x, 32), 3, 3)


def _draw_chevron(p: QPainter) -> None:
    p.setPen(_pen("#44566e", 3.3))
    p.drawLine(QPointF(21, 25), QPointF(32, 36))
    p.drawLine(QPointF(32, 36), QPointF(43, 25))




def _draw_kernel(p: QPainter) -> None:
    p.setPen(_pen("#26384d", 3.0))
    p.setBrush(QColor("#eef4fa"))
    p.drawRoundedRect(QRectF(17, 17, 30, 30), 5, 5)
    p.setBrush(QColor("#26384d"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(QRectF(25, 25, 14, 14), 3, 3)

    p.setPen(_pen("#26384d", 2.5))
    for x in (21, 29, 37, 45):
        p.drawLine(QPointF(x, 11), QPointF(x, 17))
        p.drawLine(QPointF(x, 47), QPointF(x, 53))
    for y in (21, 29, 37, 45):
        p.drawLine(QPointF(11, y), QPointF(17, y))
        p.drawLine(QPointF(47, y), QPointF(53, y))


def _draw_expand(p: QPainter) -> None:
    p.setPen(_pen("#40546d", 3.2))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawLine(QPointF(22, 42), QPointF(45, 19))
    p.drawLine(QPointF(33, 19), QPointF(45, 19))
    p.drawLine(QPointF(45, 19), QPointF(45, 31))
    p.drawRoundedRect(QRectF(14, 26, 28, 24), 4, 4)


def _draw_image(p: QPainter) -> None:
    p.setPen(_pen("#8855d8", 2.8))
    p.setBrush(QColor("#f0e9ff"))
    p.drawRoundedRect(QRectF(10, 12, 44, 40), 5, 5)
    p.setBrush(QColor("#8855d8"))
    p.drawEllipse(QPointF(41, 24), 4, 4)
    p.drawPolygon(QPolygonF([QPointF(15, 46), QPointF(28, 31), QPointF(37, 40), QPointF(45, 34), QPointF(52, 46)]))


def _draw_csv(p: QPainter) -> None:
    _draw_file(p)
    p.setPen(_pen("#249f5d", 2.2))
    for x in (25, 35, 45):
        p.drawLine(QPointF(x, 29), QPointF(x, 48))
    for y in (35, 42):
        p.drawLine(QPointF(19, y), QPointF(48, y))


def _draw_markdown(p: QPainter) -> None:
    _draw_file(p)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor("#2d80d0"))
    font = QFont("Segoe UI", 14)
    font.setBold(True)
    p.setFont(font)
    p.setPen(QColor("#2d80d0"))
    p.drawText(QRectF(18, 24, 29, 26), Qt.AlignmentFlag.AlignCenter, "M↓")


_DRAWERS = {
    "app": _draw_app,
    "folder": _draw_folder,
    "notebook": _draw_notebook,
    "file": _draw_file,
    "python": _draw_python,
    "add": _draw_add,
    "trash": _draw_trash,
    "save": _draw_save,
    "play": _draw_play,
    "run": _draw_run,
    "refresh": _draw_refresh,
    "terminal": _draw_terminal,
    "project": _draw_project,
    "search": _draw_search,
    "settings": _draw_settings,
    "home": _draw_home,
    "git": _draw_git,
    "grid": _draw_grid,
    "variables": _draw_variables,
    "kernel": _draw_kernel,
    "expand": _draw_expand,
    "stop": _draw_stop,
    "more": _draw_more,
    "edit": _draw_edit,
    "chevron": _draw_chevron,
    "image": _draw_image,
    "csv": _draw_csv,
    "markdown": _draw_markdown,
}


@lru_cache(maxsize=64)
def _painted_icon(name: str) -> QIcon:
    drawer = _DRAWERS.get(name)
    if drawer is None:
        return QIcon()

    pixmap, painter = _pixmap()
    drawer(painter)
    painter.end()
    return QIcon(pixmap)


def icon(
    name: str,
    fallback: QStyle.StandardPixmap | None = None,
) -> QIcon:
    if name in ASSET_ICONS:
        candidate_asset = asset_icon(name)
        if not candidate_asset.isNull():
            return candidate_asset

        app = QApplication.instance()
        if app is not None and fallback is not None:
            return app.style().standardIcon(fallback)
        return QIcon()

    candidate = _painted_icon(name)
    if not candidate.isNull():
        return candidate

    app = QApplication.instance()
    if app is not None and fallback is not None:
        return app.style().standardIcon(fallback)

    return QIcon()


def app_icon() -> QIcon:
    return icon("app", QStyle.StandardPixmap.SP_ComputerIcon)
