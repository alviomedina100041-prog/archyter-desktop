from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication

from app.widgets.file_explorer import FileExplorerPanel


class FileExplorerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_active_notebook_sets_clear_location_and_has_icon(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            nested = root / "julia"
            nested.mkdir()
            notebook = nested / "90200.ipynb"
            notebook.write_text("{}", encoding="utf-8")

            panel = FileExplorerPanel(str(root))
            try:
                panel.show()
                self.app.processEvents()

                panel.set_active_path(str(notebook))
                self.app.processEvents()

                self.assertEqual(
                    os.path.abspath(panel.current_directory()),
                    os.path.abspath(str(nested)),
                )
                self.assertEqual(
                    os.path.abspath(panel.selected_path() or ""),
                    os.path.abspath(str(notebook)),
                )

                index = panel.model.index(str(notebook))
                icon = panel.model.data(
                    index,
                    Qt.ItemDataRole.DecorationRole,
                )
                self.assertIsNotNone(icon)
                self.assertFalse(icon.isNull())

                self.assertFalse(panel.delete_btn.icon().isNull())
                self.assertTrue(panel.delete_btn.isVisible())

                spy = QSignalSpy(panel.delete_requested)
                panel._request_delete_selected()
                self.assertEqual(spy.count(), 1)
                self.assertEqual(
                    os.path.abspath(str(spy.at(0)[0])),
                    os.path.abspath(str(notebook)),
                )
            finally:
                panel.close()


if __name__ == "__main__":
    unittest.main()
