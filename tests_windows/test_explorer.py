from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication

from studio.explorer import ExplorerPanel


class ExplorerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_selection_icons_and_delete_signal(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / "notebooks"
            folder.mkdir()
            notebook = folder / "90200.ipynb"
            notebook.write_text("{}", encoding="utf-8")

            panel = ExplorerPanel(str(root))
            panel.show()
            self.app.processEvents()
            try:
                panel.set_active_path(str(notebook))
                self.app.processEvents()

                self.assertEqual(
                    os.path.abspath(panel.selected_path() or ""),
                    os.path.abspath(str(notebook)),
                )
                self.assertTrue(panel.delete_button.isEnabled())
                self.assertFalse(panel.delete_button.icon().isNull())

                spy = QSignalSpy(panel.delete_requested)
                panel._delete_selected()
                self.assertEqual(spy.count(), 1)
                self.assertEqual(
                    os.path.abspath(str(spy.at(0)[0])),
                    os.path.abspath(str(notebook)),
                )
            finally:
                panel.close()


if __name__ == "__main__":
    unittest.main()
