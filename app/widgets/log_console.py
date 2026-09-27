from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
)


class LogConsolePanel(QFrame):
    expand_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName("PanelCard")
        self.lines: list[str] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        header = QHBoxLayout()

        title = QPushButton("Consola / logs  ↗")
        title.setObjectName("PanelTitleButton")
        title.setToolTip("Abrir Consola / logs en una ventana grande")
        title.clicked.connect(self.expand_requested.emit)

        header.addWidget(title)
        header.addStretch(1)
        layout.addLayout(header)

        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setMaximumBlockCount(1000)
        layout.addWidget(self.console)

    def append_line(self, text: str) -> None:
        self.lines.append(text)
        if len(self.lines) > 1000:
            self.lines = self.lines[-1000:]
        self.console.appendPlainText(text)

    def all_text(self) -> str:
        return "\n".join(self.lines)
