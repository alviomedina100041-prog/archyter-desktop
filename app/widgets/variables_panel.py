from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)


class VariablesPanel(QFrame):
    refresh_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName("PanelCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        header = QHBoxLayout()
        header.setSpacing(6)

        title = QLabel("Variables")
        title.setObjectName("SectionTitle")

        self.refresh_button = QPushButton("↻")
        self.refresh_button.setToolTip("Actualizar variables")
        self.refresh_button.setFixedWidth(28)
        self.refresh_button.setFixedHeight(26)
        self.refresh_button.clicked.connect(self.refresh_requested.emit)

        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self.refresh_button)
        layout.addLayout(header)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Nombre", "Tipo", "Forma", "Valor"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(False)
        self.table.setAlternatingRowColors(False)
        layout.addWidget(self.table)

    def set_variables(self, variables: list[dict]) -> None:
        self.table.setRowCount(0)
        for item in variables:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(item.get("name", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(str(item.get("type", ""))))
            self.table.setItem(row, 2, QTableWidgetItem(str(item.get("shape", ""))))
            self.table.setItem(row, 3, QTableWidgetItem(str(item.get("value", ""))))

    def set_refreshing(self, refreshing: bool) -> None:
        self.refresh_button.setEnabled(not refreshing)
        self.refresh_button.setText("…" if refreshing else "↻")
