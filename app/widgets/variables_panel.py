from __future__ import annotations

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
    expand_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName("PanelCard")
        self.variables: list[dict] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        header = QHBoxLayout()
        header.setSpacing(4)

        self.title_button = QPushButton("Variables")
        self.title_button.setObjectName("PanelTitleButton")
        self.title_button.setToolTip("Abrir Variables en una ventana grande")
        self.title_button.clicked.connect(self.expand_requested.emit)

        self.count_label = QLabel("0")
        self.count_label.setObjectName("CountBadge")

        self.refresh_button = QPushButton("↻")
        self.refresh_button.setObjectName("IconButton")
        self.refresh_button.setToolTip("Actualizar variables")
        self.refresh_button.setFixedWidth(28)
        self.refresh_button.setFixedHeight(26)
        self.refresh_button.clicked.connect(self.refresh_requested.emit)

        self.open_button = QPushButton("Abrir ↗")
        self.open_button.setObjectName("PanelActionButton")
        self.open_button.clicked.connect(self.expand_requested.emit)

        header.addWidget(self.title_button)
        header.addWidget(self.count_label)
        header.addStretch(1)
        header.addWidget(self.refresh_button)
        header.addWidget(self.open_button)
        layout.addLayout(header)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Nombre", "Tipo"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(False)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setHorizontalScrollBarPolicy(self.table.horizontalScrollBarPolicy())
        layout.addWidget(self.table, 1)

        self.empty_label = QLabel("Pulsa ↻ para inspeccionar el kernel.")
        self.empty_label.setObjectName("MutedLabel")
        self.empty_label.setWordWrap(True)
        layout.addWidget(self.empty_label)

    def set_variables(self, variables: list[dict]) -> None:
        self.variables = [dict(item) for item in variables]
        self.table.setRowCount(0)
        self.count_label.setText(str(len(self.variables)))

        for item in self.variables[:30]:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(item.get("name", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(str(item.get("type", ""))))

        has_variables = bool(self.variables)
        self.table.setVisible(has_variables)
        self.empty_label.setVisible(not has_variables)

    def set_refreshing(self, refreshing: bool) -> None:
        self.refresh_button.setEnabled(not refreshing)
        self.refresh_button.setText("…" if refreshing else "↻")
