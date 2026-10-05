from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication

from studio.terminal import TerminalCard, detect_shell


class TerminalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_windows_shell_is_detected_and_runs_command(self) -> None:
        program, _args, label = detect_shell()
        self.assertTrue(program)
        self.assertTrue(label)

        with tempfile.TemporaryDirectory() as temp:
            terminal = TerminalCard(temp)
            try:
                command = "Get-Location" if os.name == "nt" and "PowerShell" in terminal.shell_name else "cd"
                terminal.input.setText(command)
                terminal.run_command()

                loop = QEventLoop()
                QTimer.singleShot(1300, loop.quit)
                loop.exec()

                output = terminal.output.toPlainText()
                self.assertIn(Path(temp).name.lower(), output.lower())
                self.assertNotIn("no job control", output.lower())
            finally:
                terminal.shutdown()


if __name__ == "__main__":
    unittest.main()
