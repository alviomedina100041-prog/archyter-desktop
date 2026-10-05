from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QToolButton

from studio.icons import app_icon, icon
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


    def test_session_poll_does_not_block_the_ui_thread(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            notebook = root / "responsive.ipynb"
            notebook.write_text("{}", encoding="utf-8")

            with (
                patch.object(
                    StudioWindow,
                    "_start_jupyter",
                    lambda self: None,
                ),
                patch.object(
                    StudioWindow,
                    "_start_timers",
                    lambda self: None,
                ),
            ):
                window = StudioWindow(str(root))

            try:
                window.active_document = str(notebook)
                window.manager.port = 8765

                def slow_active_session(_path):
                    time.sleep(0.45)
                    return None

                window.manager.active_session = slow_active_session

                started = time.perf_counter()
                window._refresh_session()
                elapsed = time.perf_counter() - started

                self.assertLess(
                    elapsed,
                    0.12,
                    "Session polling blocked the Qt UI thread",
                )
            finally:
                window._closing = True
                window.inspector.terminal.shutdown()
                window.close()

    def test_main_window_matches_studio_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            with (
                patch.object(
                    StudioWindow,
                    "_start_jupyter",
                    lambda self: None,
                ),
                patch.object(
                    StudioWindow,
                    "_start_timers",
                    lambda self: None,
                ),
            ):
                window = StudioWindow(str(root))

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

                for button in nav_buttons:
                    self.assertGreater(
                        visible_pixel_count(button.icon()),
                        18,
                    )

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
                self.assertFalse(
                    window.inspector.restart_button.icon().isNull()
                )
                self.assertFalse(
                    window.inspector.stop_button.icon().isNull()
                )
                self.assertFalse(
                    window.inspector.more_button.icon().isNull()
                )
            finally:
                window.inspector.terminal.shutdown()
                window.close()


if __name__ == "__main__":
    unittest.main()
