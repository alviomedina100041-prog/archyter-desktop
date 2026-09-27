import re

from PySide6.QtCore import QProcess, QProcessEnvironment, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
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

        self.process = QProcess(self)
        self.process.setWorkingDirectory(working_directory)
        self.process.setProgram("/bin/bash")
        self.process.setArguments(["--noprofile", "--norc", "-i"])

        env = QProcessEnvironment.systemEnvironment()
        env.insert("TERM", "dumb")
        env.insert("NO_COLOR", "1")
        env.insert("PS1", "$ ")
        self.process.setProcessEnvironment(env)

        self.process.readyReadStandardOutput.connect(self._read_stdout)
        self.process.readyReadStandardError.connect(self._read_stderr)
        self.process.start()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        header = QHBoxLayout()

        title = QPushButton("Terminal  ↗")
        title.setObjectName("PanelTitleButton")
        title.setToolTip("Abrir Terminal en una ventana grande")
        title.clicked.connect(self.expand_requested.emit)

        header.addWidget(title)
        header.addStretch(1)
        layout.addLayout(header)

        self.output = QPlainTextEdit()
        self.output.setObjectName("TerminalOutput")
        self.output.setReadOnly(True)
        self.output.setMaximumBlockCount(500)
        layout.addWidget(self.output, 1)

        bottom = QHBoxLayout()

        self.input = QLineEdit()
        self.input.setPlaceholderText("Comando…")
        self.input.returnPressed.connect(self.run_current_command)

        run_btn = QPushButton("Ejecutar")
        run_btn.clicked.connect(self.run_current_command)

        bottom.addWidget(self.input, 1)
        bottom.addWidget(run_btn)
        layout.addLayout(bottom)

    def _clean(self, text: str) -> str:
        return ANSI_RE.sub("", text).replace("\r", "")

    def _append(self, text: str) -> None:
        cleaned = self._clean(text).strip("\n")
        if cleaned:
            self.output.appendPlainText(cleaned)

    def _read_stdout(self) -> None:
        data = self.process.readAllStandardOutput().data().decode(errors="ignore")
        self._append(data)

    def _read_stderr(self) -> None:
        data = self.process.readAllStandardError().data().decode(errors="ignore")
        self._append(data)

    def run_current_command(self) -> None:
        command = self.input.text().strip()
        if not command:
            return

        self.output.appendPlainText(f"$ {command}")
        self.process.write((command + "\n").encode())
        self.input.clear()
