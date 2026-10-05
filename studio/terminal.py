from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

from PySide6.QtCore import QProcess, QProcessEnvironment, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from .icons import icon

ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def detect_shell() -> tuple[str, list[str], str]:
    if os.name == "nt":
        pwsh = shutil.which("pwsh.exe") or shutil.which("pwsh")
        if pwsh:
            return pwsh, ["-NoLogo", "-NoProfile", "-NoExit", "-Command", "-"], "PowerShell 7"

        powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        if powershell:
            return powershell, ["-NoLogo", "-NoProfile", "-NoExit", "-Command", "-"], "Windows PowerShell"

        cmd = os.environ.get("COMSPEC") or shutil.which("cmd.exe") or "cmd.exe"
        return cmd, ["/Q"], "Command Prompt"

    shell = os.environ.get("SHELL") or shutil.which("bash") or "/bin/sh"
    return shell, [], Path(shell).name


class TerminalCard(QFrame):
    expand_requested = Signal()

    def __init__(self, working_directory: str):
        super().__init__()
        self.setObjectName("TerminalCard")
        self.working_directory = os.path.abspath(working_directory)
        self.process = QProcess(self)

        program, args, label = detect_shell()
        self.shell_name = label
        self.process.setProgram(program)
        self.process.setArguments(args)
        self.process.setWorkingDirectory(self.working_directory)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)

        env = QProcessEnvironment.systemEnvironment()
        env.insert("PYTHONUTF8", "1")
        env.insert("NO_COLOR", "1")
        env.insert("TERM", "dumb")
        self.process.setProcessEnvironment(env)

        self.process.readyReadStandardOutput.connect(self._read_output)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(9, 8, 9, 8)
        layout.setSpacing(6)

        header = QHBoxLayout()
        title = QPushButton("Terminal")
        title.setIcon(icon("terminal"))
        title.setFlat(True)
        title.clicked.connect(self.expand_requested.emit)
        header.addWidget(title)
        header.addStretch(1)
        layout.addLayout(header)

        self.output = QPlainTextEdit()
        self.output.setObjectName("Terminal")
        self.output.setReadOnly(True)
        self.output.setMaximumBlockCount(400)
        self.output.setPlaceholderText(f"{label} listo para comandos…")
        layout.addWidget(self.output, 1)

        row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Comando…")
        self.input.returnPressed.connect(self.run_command)
        self.run_button = QPushButton("Ejecutar")
        self.run_button.clicked.connect(self.run_command)
        row.addWidget(self.input, 1)
        row.addWidget(self.run_button)
        layout.addLayout(row)

        self.process.start()
        if not self.process.waitForStarted(2500):
            self.output.setPlainText(f"No se pudo iniciar {label}.")
            self.input.setEnabled(False)
            self.run_button.setEnabled(False)

    def _read_output(self) -> None:
        data = bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="replace")
        text = ANSI_RE.sub("", data).replace("\r", "").strip("\n")
        if text:
            self.output.appendPlainText(text)

    def send_command(self, command: str) -> None:
        command = command.strip()
        if not command or self.process.state() == QProcess.ProcessState.NotRunning:
            return
        self.output.appendPlainText(f"> {command}")
        self.process.write((command + os.linesep).encode("utf-8"))

    def run_command(self) -> None:
        command = self.input.text().strip()
        if not command:
            return
        self.send_command(command)
        self.input.clear()

    def set_working_directory(self, path: str) -> None:
        target = os.path.abspath(path)
        self.working_directory = target
        if self.process.state() == QProcess.ProcessState.NotRunning:
            self.process.setWorkingDirectory(target)
            return

        if os.name == "nt":
            escaped = target.replace("'", "''")
            if "PowerShell" in self.shell_name:
                self.process.write(f"Set-Location -LiteralPath '{escaped}'\r\n".encode("utf-8"))
            else:
                self.process.write(f'cd /d "{target}"\r\n'.encode("utf-8"))
        else:
            import shlex
            self.process.write(f"cd -- {shlex.quote(target)}\n".encode("utf-8"))

    def shutdown(self) -> None:
        if self.process.state() == QProcess.ProcessState.NotRunning:
            return
        if os.name == "nt" and "PowerShell" in self.shell_name:
            self.process.write(b"exit\r\n")
        else:
            self.process.write(b"exit\n")
        if not self.process.waitForFinished(900):
            self.process.terminate()
            if not self.process.waitForFinished(900):
                self.process.kill()
                self.process.waitForFinished(500)
