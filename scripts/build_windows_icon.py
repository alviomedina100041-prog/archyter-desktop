from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer


def build_icon(source_path: str, target_path: str) -> Path:
    source = Path(source_path).resolve()
    target = Path(target_path).resolve()

    renderer = QSvgRenderer(str(source))
    if not renderer.isValid():
        raise RuntimeError(f"No se pudo leer el SVG: {source}")

    image = QImage(
        256,
        256,
        QImage.Format.Format_ARGB32,
    )
    image.fill(QColor(0, 0, 0, 0))

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    renderer.render(
        painter,
        QRectF(0, 0, 256, 256),
    )
    painter.end()

    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not image.save(str(target), "ICO"):
        raise RuntimeError(
            f"No se pudo generar el icono de Windows: {target}"
        )

    return target


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: build_windows_icon.py input.svg output.ico")

    build_icon(sys.argv[1], sys.argv[2])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
