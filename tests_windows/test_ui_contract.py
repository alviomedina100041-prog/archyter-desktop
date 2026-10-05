from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QPlainTextEdit, QToolButton

from studio.icons import app_icon, icon
from studio.native_kernel import NativeKernelController
from studio.native_notebook import NativeNotebookEditor
from studio.window import StudioWindow


def visible_pixel_count(qicon) -> int:
    pixmap = qicon.pixmap(28, 28)
    if pixmap.isNull():
        return 0

    image = pixmap.toImage()
    count = 0

    for y in range(image.height()):
        for x in range(image.width()):
            color = QColor.fromRgba(image.pixel(x, y))
            if color.alpha() > 20:
                count += 1

    return count


class UiContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def _window(self, root: Path) -> StudioWindow:
        patcher = patch.object(
            NativeKernelController,
            "start",
            lambda self: None,
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        return StudioWindow(str(root))

    def test_painted_icons_are_visibly_rendered(self) -> None:
        required = (
            "app",
            "home",
            "search",
            "git",
            "run",
            "grid",
            "folder",
            "notebook",
            "python",
            "save",
            "play",
            "kernel",
            "terminal",
            "project",
            "trash",
            "refresh",
            "settings",
            "expand",
        )

        for name in required:
            with self.subTest(icon=name):
                self.assertGreater(
                    visible_pixel_count(icon(name)),
                    18,
                    f"{name} rendered as an empty icon",
                )

        self.assertGreater(visible_pixel_count(app_icon()), 18)

    def test_native_notebook_load_is_immediate_and_keyboard_editable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            notebook = root / "instant.ipynb"
            notebook.write_text(
                json.dumps(
                    {
                        "cells": [],
                        "metadata": {},
                        "nbformat": 4,
                        "nbformat_minor": 5,
                    }
                ),
                encoding="utf-8",
            )

            window = self._window(root)
            try:
                started = time.perf_counter()
                window._open_file(str(notebook))
                elapsed = time.perf_counter() - started

                self.assertLess(
                    elapsed,
                    0.12,
                    "Native notebook opening is unexpectedly slow",
                )
                self.assertEqual(
                    window.active_document,
                    str(notebook.resolve()),
                )
                self.assertIsInstance(
                    window.notebook_editor,
                    NativeNotebookEditor,
                )
                self.assertTrue(window.notebook_editor.cells)
                self.assertIsInstance(
                    window.notebook_editor.cells[0].editor,
                    QPlainTextEdit,
                )

                editor = window.notebook_editor.cells[0].editor
                editor.insertPlainText("print('hola')")
                self.assertIn("print('hola')", editor.toPlainText())
            finally:
                window._closing = True
                window.inspector.terminal.shutdown()
                window.kernel.shutdown()
                window.close()

    def test_native_notebook_saves_valid_ipynb(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            notebook = root / "save.ipynb"
            notebook.write_text(
                '{"cells":[],"metadata":{},"nbformat":4,"nbformat_minor":5}',
                encoding="utf-8",
            )

            window = self._window(root)
            try:
                window._open_file(str(notebook))
                cell = window.notebook_editor.cells[0]
                cell.editor.setPlainText("x = 42")
                window._save()

                payload = json.loads(
                    notebook.read_text(encoding="utf-8")
                )
                self.assertEqual(
                    payload["cells"][0]["cell_type"],
                    "code",
                )
                self.assertIn(
                    "x = 42",
                    "".join(payload["cells"][0]["source"]),
                )
            finally:
                window._closing = True
                window.inspector.terminal.shutdown()
                window.kernel.shutdown()
                window.close()

    def test_main_window_matches_studio_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            window = self._window(root)

            try:
                window.show()
                self.app.processEvents()

                self.assertEqual(
                    window.windowTitle(),
                    "Archyter Studio",
                )
                self.assertGreater(
                    visible_pixel_count(window.windowIcon()),
                    18,
                )
                self.assertIsInstance(
                    window.new_button,
                    QToolButton,
                )
                self.assertEqual(
                    [
                        action.text()
                        for action in window.new_button.menu().actions()
                    ],
                    [
                        "Notebook",
                        "Carpeta",
                        "Archivo de texto",
                    ],
                )

                for button in (
                    window.new_button,
                    window.save_button,
                    window.run_button,
                    window.kernel_button,
                    window.explorer.new_button,
                    window.explorer.delete_button,
                ):
                    self.assertGreater(
                        visible_pixel_count(button.icon()),
                        18,
                    )

                nav_buttons = window.findChildren(
                    QToolButton,
                    "NavButton",
                )
                self.assertEqual(len(nav_buttons), 5)

                self.assertGreaterEqual(
                    window.explorer.minimumWidth(),
                    240,
                )
                self.assertLessEqual(
                    window.explorer.maximumWidth(),
                    320,
                )
                self.assertGreaterEqual(
                    window.inspector.minimumWidth(),
                    300,
                )
                self.assertLessEqual(
                    window.inspector.maximumWidth(),
                    370,
                )

                sizes = window.splitter.sizes()
                self.assertEqual(len(sizes), 3)
                self.assertGreater(sizes[1], sizes[0])
                self.assertGreater(sizes[1], sizes[2])

                self.assertEqual(
                    window.document_tab.objectName(),
                    "DocumentTab",
                )
                self.assertEqual(
                    window.inspector.kernel_card.objectName(),
                    "Card",
                )
                self.assertIsInstance(
                    window.notebook_editor,
                    NativeNotebookEditor,
                )
            finally:
                window._closing = True
                window.inspector.terminal.shutdown()
                window.kernel.shutdown()
                window.close()


if __name__ == "__main__":
    unittest.main()
