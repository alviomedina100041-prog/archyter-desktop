from __future__ import annotations

import tempfile
import unittest

from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication

from app.widgets.mini_terminal import MiniTerminalPanel


class MiniTerminalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_shell_has_no_interactive_job_control_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            terminal = MiniTerminalPanel(temp)
            try:
                terminal.input.setText("pwd")
                terminal.run_current_command()

                loop = QEventLoop()
                QTimer.singleShot(700, loop.quit)
                loop.exec()

                output = terminal.output.toPlainText()
                self.assertIn(temp, output)
                self.assertNotIn("no job control", output.lower())
                self.assertNotIn(
                    "cannot set terminal process group",
                    output.lower(),
                )
            finally:
                terminal.shutdown()
                terminal.close()


if __name__ == "__main__":
    unittest.main()
