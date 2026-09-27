from PySide6.QtCore import QProcess
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QPushButton, QVBoxLayout


class MiniTerminalPanel(QFrame):
    def __init__(self, working_directory: str):
        super().__init__()
        self.setObjectName("PanelCard")

        self.process = QProcess(self)
        self.process.setWorkingDirectory(working_directory)
        self.process.setProgram("/bin/bash")
        self.process.setArguments(["-i"])
        self.process.readyReadStandardOutput.connect(self._read_stdout)
        self.process.readyReadStandardError.connect(self._read_stderr)
        self.process.start()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        title = QLabel("Terminal")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output, 1)

        bottom = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Escribe un comando y presiona Enter...")
        self.input.returnPressed.connect(self.run_current_command)

        run_btn = QPushButton("Ejecutar")
        run_btn.clicked.connect(self.run_current_command)

        bottom.addWidget(self.input, 1)
        bottom.addWidget(run_btn)
        layout.addLayout(bottom)

    def _read_stdout(self) -> None:
        data = self.process.readAllStandardOutput().data().decode(errors="ignore")
        if data:
            self.output.appendPlainText(data.rstrip())

    def _read_stderr(self) -> None:
        data = self.process.readAllStandardError().data().decode(errors="ignore")
        if data:
            self.output.appendPlainText(data.rstrip())

    def run_current_command(self) -> None:
        command = self.input.text().strip()
        if not command:
            return
        self.output.appendPlainText(f"$ {command}")
        self.process.write((command + "\n").encode())
        self.input.clear()
