from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication

from studio.window import StudioWindow


def main() -> int:
    app = QApplication.instance() or QApplication([])

    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        (root / "notebooks").mkdir()
        (root / "data").mkdir()
        (root / "notebooks" / "90200.ipynb").write_text("{}", encoding="utf-8")
        (root / "data" / "ventas.csv").write_text("fecha,ventas\n2026-01-01,100\n", encoding="utf-8")
        (root / "datos.py").write_text("x = 42\n", encoding="utf-8")

        with (
            patch.object(StudioWindow, "_start_jupyter", lambda self: None),
            patch.object(StudioWindow, "_start_timers", lambda self: None),
        ):
            window = StudioWindow(str(root))

        window.resize(1480, 900)
        window.show()
        app.processEvents()

        output_dir = Path("artifacts")
        output_dir.mkdir(exist_ok=True)
        output = output_dir / "archyter-studio-smoke.png"

        pixmap = window.grab()
        if pixmap.isNull():
            raise RuntimeError("Qt no pudo renderizar la ventana de Archyter Studio.")
        if pixmap.width() < 1100 or pixmap.height() < 700:
            raise RuntimeError(f"Render inesperado: {pixmap.width()}x{pixmap.height()}")
        if not pixmap.save(str(output), "PNG"):
            raise RuntimeError("No se pudo guardar la captura de prueba.")

        window.inspector.terminal.shutdown()
        window.close()

    print(f"UI smoke render: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
