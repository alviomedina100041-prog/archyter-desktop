from __future__ import annotations

import os
import re
import shlex

from PySide6.QtCore import QProcess, QProcessEnvironment, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)


ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


class MiniTerminalPanel(QFrame):
    expand_requested = Signal()

    def __init__(self, working_directory: str):
        super().__init__()
        self.setObjectName("PanelCard")
        self.working_directory = os.path.abspath(working_directory)

        self.process = QProcess(self)
        self.process.setWorkingDirectory(self.working_directory)
        self.process.setProgram("/bin/bash")

        # QProcess does not provide a PTY. Starting bash with -i therefore
        # prints "no job control" warnings. A persistent non-interactive bash
        # still preserves cd/export state between commands without those
        # terminal errors.
        self.process.setArguments(["--noprofile", "--norc"])
        self.process.setProcessChannelMode(QProcess.MergedChannels)

        env = QProcessEnvironment.systemEnvironment()
        env.insert("TERM", "dumb")
        env.insert("NO_COLOR", "1")
        self.process.setProcessEnvironment(env)

        self.process.readyReadStandardOutput.connect(self._read_output)
        self.process.finished.connect(self._process_finished)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        header = QHBoxLayout()
        header.setSpacing(4)

        self.title_button = QPushButton("Terminal")
        self.title_button.setObjectName("PanelTitleButton")
        self.title_button.setToolTip("Abrir Terminal en una ventana grande")
        self.title_button.clicked.connect(self.expand_requested.emit)

        self.open_button = QPushButton("Abrir ↗")
        self.open_button.setObjectName("PanelActionButton")
        self.open_button.setToolTip("Abrir terminal grande")
        self.open_button.clicked.connect(self.expand_requested.emit)

        header.addWidget(self.title_button)
        header.addStretch(1)
        header.addWidget(self.open_button)
        layout.addLayout(header)

        self.output = QPlainTextEdit()
        self.output.setObjectName("TerminalOutput")
        self.output.setReadOnly(True)
        self.output.setMaximumBlockCount(300)
        self.output.setPlaceholderText("Salida de comandos…")
        layout.addWidget(self.output, 1)

        bottom = QHBoxLayout()
        bottom.setSpacing(5)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Comando…")
        self.input.returnPressed.connect(self.run_current_command)

        self.run_button = QPushButton("Ejecutar")
        self.run_button.setObjectName("CompactButton")
        self.run_button.clicked.connect(self.run_current_command)

        bottom.addWidget(self.input, 1)
        bottom.addWidget(self.run_button)
        layout.addLayout(bottom)

        self.process.start()
        if not self.process.waitForStarted(1500):
            self.output.setPlainText("No se pudo iniciar /bin/bash.")
            self.input.setEnabled(False)
            self.run_button.setEnabled(False)

    def _clean(self, text: str) -> str:
        return ANSI_RE.sub("", text).replace("\r", "")

    def _append(self, text: str) -> None:
        cleaned = self._clean(text).strip("\n")
        if cleaned:
            self.output.appendPlainText(cleaned)

    def _read_output(self) -> None:
        data = self.process.readAllStandardOutput().data().decode(errors="ignore")
        self._append(data)

    def _process_finished(self, *_args) -> None:
        if self.input.isEnabled():
            self._append("Terminal finalizada.")
        self.input.setEnabled(False)
        self.run_button.setEnabled(False)

    def run_current_command(self) -> None:
        command = self.input.text().strip()
        if not command:
            return

        if self.process.state() == QProcess.NotRunning:
            self._append("La terminal no está activa.")
            return

        self.output.appendPlainText(f"$ {command}")
        self.process.write((command + "\n").encode())
        self.input.clear()

    def set_working_directory(self, path: str) -> None:
        target = os.path.abspath(path)
        self.working_directory = target

        if self.process.state() != QProcess.NotRunning:
            self.process.write(
                f"cd -- {shlex.quote(target)}\n".encode()
            )

    def shutdown(self) -> None:
        if self.process.state() == QProcess.NotRunning:
            return

        self.process.write(b"exit\n")
        if not self.process.waitForFinished(600):
            self.process.terminate()
            if not self.process.waitForFinished(600):
                self.process.kill()
                self.process.waitForFinished(400)

    def closeEvent(self, event) -> None:
        self.shutdown()
        super().closeEvent(event)
