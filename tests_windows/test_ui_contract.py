from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication, QToolButton

from studio.window import StudioWindow


class UiContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_main_window_matches_studio_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with (
                patch.object(StudioWindow, "_start_jupyter", lambda self: None),
                patch.object(StudioWindow, "_start_timers", lambda self: None),
            ):
                window = StudioWindow(str(root))

            try:
                window.show()
                self.app.processEvents()

                self.assertEqual(window.windowTitle(), "Archyter Studio")
                self.assertFalse(window.windowIcon().isNull())
                self.assertIsInstance(window.new_button, QToolButton)
                self.assertEqual(
                    [action.text() for action in window.new_button.menu().actions()],
                    ["Notebook", "Carpeta", "Archivo de texto"],
                )
                self.assertFalse(window.save_button.icon().isNull())
                self.assertFalse(window.run_button.icon().isNull())
                self.assertFalse(window.kernel_button.icon().isNull())
                self.assertFalse(window.explorer.delete_button.icon().isNull())

                self.assertGreaterEqual(window.explorer.minimumWidth(), 235)
                self.assertLessEqual(window.explorer.maximumWidth(), 315)
                self.assertGreaterEqual(window.inspector.minimumWidth(), 290)
                self.assertLessEqual(window.inspector.maximumWidth(), 360)

                sizes = window.splitter.sizes()
                self.assertEqual(len(sizes), 3)
                self.assertGreater(sizes[1], sizes[0])
                self.assertGreater(sizes[1], sizes[2])
            finally:
                window.inspector.terminal.shutdown()
                window.close()


if __name__ == "__main__":
    unittest.main()
