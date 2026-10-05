from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PySide6.QtWidgets import QApplication

from studio.native_kernel import NativeKernelController
from studio.window import StudioWindow


def main() -> int:
    app = QApplication.instance() or QApplication([])

    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        (root / "notebooks").mkdir()
        (root / "data").mkdir()

        notebook = root / "notebooks" / "90200.ipynb"
        notebook.write_text(
            json.dumps(
                {
                    "cells": [
                        {
                            "cell_type": "code",
                            "execution_count": 1,
                            "metadata": {},
                            "outputs": [
                                {
                                    "name": "stdout",
                                    "output_type": "stream",
                                    "text": "hola mundo\n",
                                }
                            ],
                            "source": ["print('hola mundo')"],
                        },
                        {
                            "cell_type": "code",
                            "execution_count": None,
                            "metadata": {},
                            "outputs": [],
                            "source": [""],
                        },
                    ],
                    "metadata": {},
                    "nbformat": 4,
                    "nbformat_minor": 5,
                }
            ),
            encoding="utf-8",
        )
        (root / "data" / "ventas.csv").write_text(
            "fecha,ventas\n2026-01-01,100\n",
            encoding="utf-8",
        )
        (root / "datos.py").write_text(
            "x = 42\n",
            encoding="utf-8",
        )

        with patch.object(
            NativeKernelController,
            "start",
            lambda self: None,
        ):
            window = StudioWindow(str(root))

        window.resize(1480, 900)
        window.show()
        window._open_file(str(notebook))
        app.processEvents()

        output_dir = Path("artifacts")
        output_dir.mkdir(exist_ok=True)
        output = output_dir / "archyter-studio-smoke.png"

        pixmap = window.grab()
        if pixmap.isNull():
            raise RuntimeError(
                "Qt no pudo renderizar la ventana de Archyter Studio."
            )
        if pixmap.width() < 1100 or pixmap.height() < 700:
            raise RuntimeError(
                f"Render inesperado: {pixmap.width()}x{pixmap.height()}"
            )
        if not pixmap.save(str(output), "PNG"):
            raise RuntimeError(
                "No se pudo guardar la captura de prueba."
            )

        window.inspector.terminal.shutdown()
        window.kernel.shutdown()
        window.close()

    print(f"UI smoke render: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
