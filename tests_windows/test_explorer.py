from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from PySide6.QtCore import QRect
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication

from studio.delegates import CleanProjectTree, CleanTreeDelegate
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

                selected = panel.selected_path()
                self.assertIsNotNone(selected)
                self.assertTrue(os.path.samefile(str(selected), str(notebook)))
                self.assertTrue(panel.delete_button.isEnabled())
                self.assertFalse(panel.delete_button.icon().isNull())
                self.assertIsInstance(panel.tree, CleanProjectTree)
                self.assertIsInstance(
                    panel.tree.itemDelegate(),
                    CleanTreeDelegate,
                )

                # A file has no branch chevron. Its gutter must still be
                # explicitly repainted, otherwise Windows can leave a stale
                # colored square beside the selected row.
                branch_image = QImage(
                    52,
                    28,
                    QImage.Format.Format_ARGB32,
                )
                branch_image.fill(QColor("#cc0000"))

                branch_painter = QPainter(branch_image)
                panel.tree.drawBranches(
                    branch_painter,
                    QRect(0, 0, 52, 28),
                    panel.model.index(str(notebook)),
                )
                branch_painter.end()

                expected = QColor("#fbfdff")
                for y in range(branch_image.height()):
                    for x in range(branch_image.width()):
                        self.assertEqual(
                            QColor.fromRgba(
                                branch_image.pixel(x, y)
                            ).name(),
                            expected.name(),
                        )

                index = panel.model.index(str(notebook))
                rect = panel.tree.visualRect(index)
                grab = panel.tree.viewport().grab().toImage()
                suspicious = 0
                y0 = max(0, rect.top())
                y1 = min(grab.height(), rect.bottom() + 1)
                x1 = min(grab.width(), max(48, rect.left()))

                for y in range(y0, y1):
                    for x in range(0, x1):
                        color = QColor.fromRgba(grab.pixel(x, y))
                        is_dark = (
                            color.red() < 45
                            and color.green() < 45
                            and color.blue() < 45
                            and color.alpha() > 220
                        )
                        is_red_block = (
                            color.red() > 145
                            and color.green() < 90
                            and color.blue() < 100
                            and color.alpha() > 220
                        )
                        is_blue_block = (
                            color.blue() > 135
                            and color.red() < 90
                            and color.green() < 150
                            and color.alpha() > 220
                        )
                        if is_dark or is_red_block or is_blue_block:
                            suspicious += 1

                self.assertLess(
                    suspicious,
                    160,
                    "Explorer branch gutter contains a solid color block",
                )

                spy = QSignalSpy(panel.delete_requested)
                panel._delete_selected()
                self.assertEqual(spy.count(), 1)
                self.assertTrue(
                    os.path.samefile(str(spy.at(0)[0]), str(notebook))
                )
            finally:
                panel.close()


if __name__ == "__main__":
    unittest.main()
