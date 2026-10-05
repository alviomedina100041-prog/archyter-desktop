from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from .icons import icon
from .terminal import TerminalCard


class InspectorPanel(QFrame):
    refresh_variables = Signal()
    restart_kernel = Signal()

    def __init__(self, working_directory: str):
        super().__init__()
        self.setObjectName("Inspector")
        self.variables: list[dict] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(9, 9, 9, 9)
        layout.setSpacing(8)

        heading = QHBoxLayout()
        title = QLabel("INSPECTOR")
        title.setObjectName("SectionTitle")
        session = QLabel("sesión")
        session.setObjectName("Muted")
        heading.addWidget(title)
        heading.addStretch(1)
        heading.addWidget(session)
        layout.addLayout(heading)

        kernel_card = QFrame()
        kernel_card.setObjectName("Card")
        k = QVBoxLayout(kernel_card)
        k.setContentsMargins(10, 9, 10, 9)
        k.setSpacing(5)

        row = QHBoxLayout()
        kernel_title = QLabel("⚙  Kernel")
        kernel_title.setObjectName("SectionTitle")
        self.kernel_badge = QLabel("detenido")
        self.kernel_badge.setObjectName("KernelBadge")
        row.addWidget(kernel_title)
        row.addStretch(1)
        row.addWidget(self.kernel_badge)
        k.addLayout(row)

        self.kernel_name = QLabel("Python 3")
        self.kernel_name.setObjectName("SectionTitle")
        self.kernel_detail = QLabel("Esperando sesión…")
        self.kernel_detail.setObjectName("Muted")
        k.addWidget(self.kernel_name)
        k.addWidget(self.kernel_detail)

        self.restart_button = QPushButton("Reiniciar kernel")
        self.restart_button.setIcon(icon("refresh"))
        self.restart_button.clicked.connect(self.restart_kernel.emit)
        k.addWidget(self.restart_button)
        layout.addWidget(kernel_card)

        variables_card = QFrame()
        variables_card.setObjectName("Card")
        v = QVBoxLayout(variables_card)
        v.setContentsMargins(8, 8, 8, 8)
        v.setSpacing(5)

        vh = QHBoxLayout()
        variables_title = QLabel("Variables")
        variables_title.setObjectName("SectionTitle")
        self.count = QLabel("0")
        self.count.setObjectName("Badge")
        refresh = QPushButton()
        refresh.setIcon(icon("refresh"))
        refresh.setFixedWidth(32)
        refresh.setToolTip("Actualizar variables")
        refresh.clicked.connect(self.refresh_variables.emit)
        vh.addWidget(variables_title)
        vh.addWidget(self.count)
        vh.addStretch(1)
        vh.addWidget(refresh)
        v.addLayout(vh)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Nombre", "Tipo", "Valor"])
        self.table.verticalHeader().hide()
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        v.addWidget(self.table, 1)
        layout.addWidget(variables_card, 1)

        self.terminal = TerminalCard(working_directory)
        self.terminal.setMinimumHeight(190)
        layout.addWidget(self.terminal)

    def update_kernel(self, name: str, state: str, detail: str) -> None:
        self.kernel_name.setText(name or "Python 3")
        self.kernel_badge.setText(state or "desconocido")
        self.kernel_detail.setText(detail)

    def set_variables(self, variables: list[dict]) -> None:
        self.variables = [dict(item) for item in variables]
        self.count.setText(str(len(self.variables)))
        self.table.setRowCount(0)
        for item in self.variables[:80]:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(item.get("name", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(str(item.get("type", ""))))
            value = item.get("value") or item.get("shape") or ""
            self.table.setItem(row, 2, QTableWidgetItem(str(value)))
