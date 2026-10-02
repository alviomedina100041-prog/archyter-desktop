from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication, QToolButton

from app.window import MainWindow


class WindowSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_window_builds_with_creation_menu_and_active_document_bar(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            nested = root / "julia"
            nested.mkdir()
            notebook = nested / "90200.ipynb"
            notebook.write_text("{}", encoding="utf-8")

            with (
                patch.object(MainWindow, "_start_jupyter", lambda self: None),
                patch.object(MainWindow, "_start_timers", lambda self: None),
            ):
                window = MainWindow(str(root))

            try:
                self.assertIsInstance(window.new_button, QToolButton)
                self.assertIsNotNone(window.new_button.menu())
                self.assertEqual(
                    [action.text() for action in window.new_button.menu().actions()],
                    ["Notebook", "Carpeta", "Archivo de texto"],
                )

                window._open_path(str(notebook))
                self.app.processEvents()

                self.assertEqual(window.document_label.text(), "90200.ipynb")
                self.assertEqual(
                    Path(window.file_explorer.current_directory()),
                    nested,
                )
                self.assertFalse(window.windowIcon().isNull())
                self.assertFalse(window.new_button.icon().isNull())
                self.assertFalse(window.save_button.icon().isNull())
                self.assertFalse(window.run_button.icon().isNull())
            finally:
                window.terminal_panel.shutdown()
                window.close()


if __name__ == "__main__":
    unittest.main()
