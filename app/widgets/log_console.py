from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
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
        header.setSpacing(4)

        title = QPushButton("Consola / logs")
        title.setObjectName("PanelTitleButton")
        title.setToolTip("Abrir Consola / logs en una ventana grande")
        title.clicked.connect(self.expand_requested.emit)

        self.count_label = QLabel("0")
        self.count_label.setObjectName("CountBadge")

        open_button = QPushButton("Abrir ↗")
        open_button.setObjectName("PanelActionButton")
        open_button.clicked.connect(self.expand_requested.emit)

        header.addWidget(title)
        header.addWidget(self.count_label)
        header.addStretch(1)
        header.addWidget(open_button)
        layout.addLayout(header)

        self.console = QPlainTextEdit()
        self.console.setObjectName("LogPreview")
        self.console.setReadOnly(True)
        self.console.setMaximumBlockCount(120)
        self.console.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.console.setPlaceholderText("Sin eventos recientes.")
        layout.addWidget(self.console, 1)

    def append_line(self, text: str) -> None:
        self.lines.append(text)
        if len(self.lines) > 1000:
            self.lines = self.lines[-1000:]

        self.count_label.setText(str(len(self.lines)))
        self.console.appendPlainText(text)

        # Keep the preview focused on the newest server/app event.
        bar = self.console.verticalScrollBar()
        bar.setValue(bar.maximum())

    def all_text(self) -> str:
        return "\n".join(self.lines)
