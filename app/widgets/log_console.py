from PySide6.QtWidgets import QFrame, QLabel, QPlainTextEdit, QVBoxLayout


class LogConsolePanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("PanelCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        title = QLabel("Consola del kernel / logs")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        layout.addWidget(self.console)

    def append_line(self, text: str) -> None:
        self.console.appendPlainText(text)
