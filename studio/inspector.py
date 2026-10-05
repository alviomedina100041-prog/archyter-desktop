from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from .animated import AnimatedToolButton, add_soft_shadow
from .icons import icon
from .terminal import TerminalCard


class InspectorPanel(QFrame):
    refresh_variables = Signal()
    restart_kernel = Signal()
    stop_kernel = Signal()
    kernel_menu_requested = Signal()
    terminal_expand_requested = Signal()

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

        self.kernel_card = QFrame()
        self.kernel_card.setObjectName("Card")
        add_soft_shadow(self.kernel_card, blur=16, y_offset=2, alpha=20)

        k = QVBoxLayout(self.kernel_card)
        k.setContentsMargins(10, 9, 10, 9)
        k.setSpacing(7)

        kernel_header = QHBoxLayout()
        kernel_header.setSpacing(5)

        kernel_title_icon = QLabel()
        kernel_title_icon.setPixmap(icon("kernel").pixmap(15, 15))
        kernel_title_icon.setFixedSize(17, 17)

        kernel_title = QLabel("Kernel")
        kernel_title.setObjectName("SectionTitle")

        kernel_header.addWidget(kernel_title_icon)
        kernel_header.addWidget(kernel_title)
        kernel_header.addStretch(1)
        k.addLayout(kernel_header)

        identity = QHBoxLayout()
        identity.setSpacing(8)

        python_logo = QLabel()
        python_logo.setPixmap(icon("python").pixmap(42, 42))
        python_logo.setFixedSize(46, 46)
        python_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        identity.addWidget(python_logo)

        name_column = QVBoxLayout()
        name_column.setSpacing(1)
        self.kernel_name = QLabel("Python 3")
        self.kernel_name.setObjectName("SectionTitle")
        self.kernel_badge = QLabel("●  detenido")
        self.kernel_badge.setObjectName("KernelBadge")
        self.kernel_badge.setMaximumWidth(92)
        name_column.addWidget(self.kernel_name)
        name_column.addWidget(self.kernel_badge)
        identity.addLayout(name_column)
        identity.addStretch(1)

        self.restart_button = AnimatedToolButton(base_icon=17, hover_icon=19)
        self.restart_button.setObjectName("IconButton")
        self.restart_button.setIcon(icon("refresh"))
        self.restart_button.setToolTip("Reiniciar kernel")
        self.restart_button.clicked.connect(self.restart_kernel.emit)

        self.stop_button = AnimatedToolButton(base_icon=15, hover_icon=17)
        self.stop_button.setObjectName("IconButton")
        self.stop_button.setIcon(icon("stop"))
        self.stop_button.setToolTip("Detener kernel")
        self.stop_button.clicked.connect(self.stop_kernel.emit)

        self.more_button = AnimatedToolButton(base_icon=16, hover_icon=18)
        self.more_button.setObjectName("IconButton")
        self.more_button.setIcon(icon("more"))
        self.more_button.setToolTip("Detalles del kernel")
        self.more_button.clicked.connect(self.kernel_menu_requested.emit)

        identity.addWidget(self.restart_button)
        identity.addWidget(self.stop_button)
        identity.addWidget(self.more_button)
        k.addLayout(identity)

        self.kernel_detail = QLabel("Abre un notebook para iniciar.")
        self.kernel_detail.setObjectName("Muted")
        self.kernel_detail.setWordWrap(True)
        k.addWidget(self.kernel_detail)
        layout.addWidget(self.kernel_card)

        self.variables_card = QFrame()
        self.variables_card.setObjectName("Card")
        add_soft_shadow(self.variables_card, blur=14, y_offset=2, alpha=17)

        v = QVBoxLayout(self.variables_card)
        v.setContentsMargins(8, 8, 8, 8)
        v.setSpacing(5)

        vh = QHBoxLayout()
        vh.setSpacing(5)

        self.variables_toggle = AnimatedToolButton(base_icon=13, hover_icon=15)
        self.variables_toggle.setObjectName("FlatAction")
        self.variables_toggle.setIcon(icon("chevron"))
        self.variables_toggle.setToolTip("Mostrar u ocultar variables")
        self.variables_toggle.clicked.connect(self._toggle_variables)

        variables_title = QLabel("Variables")
        variables_title.setObjectName("SectionTitle")

        self.count = QLabel("0")
        self.count.setObjectName("Badge")

        self.refresh_button = AnimatedToolButton(base_icon=16, hover_icon=18)
        self.refresh_button.setObjectName("IconButton")
        self.refresh_button.setIcon(icon("refresh"))
        self.refresh_button.setToolTip("Actualizar variables")
        self.refresh_button.clicked.connect(self.refresh_variables.emit)

        vh.addWidget(self.variables_toggle)
        vh.addWidget(variables_title)
        vh.addWidget(self.count)
        vh.addStretch(1)
        vh.addWidget(self.refresh_button)
        v.addLayout(vh)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Nombre", "Tipo", "Valor"])
        self.table.verticalHeader().hide()
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        self.table.horizontalHeader().setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.Stretch,
        )
        v.addWidget(self.table, 1)
        layout.addWidget(self.variables_card, 1)

        self.terminal = TerminalCard(working_directory)
        self.terminal.setMinimumHeight(205)
        self.terminal.expand_requested.connect(
            self.terminal_expand_requested.emit
        )
        layout.addWidget(self.terminal)

    def _toggle_variables(self) -> None:
        self.table.setVisible(not self.table.isVisible())

    def update_kernel(self, name: str, state: str, detail: str) -> None:
        self.kernel_name.setText(name or "Python 3")
        normalized = (state or "desconocido").lower()
        display = {
            "idle": "Activo",
            "busy": "Ejecutando",
            "starting": "Iniciando",
            "sin sesión": "Sin sesión",
            "detenido": "Detenido",
        }.get(normalized, state or "desconocido")
        self.kernel_badge.setText(f"●  {display}")
        self.kernel_detail.setText(detail)

        has_kernel = normalized not in {
            "sin sesión",
            "detenido",
            "dead",
            "desconocido",
        }
        self.restart_button.setEnabled(has_kernel)
        self.stop_button.setEnabled(has_kernel)
        self.more_button.setEnabled(has_kernel)

    def set_variables(self, variables: list[dict]) -> None:
        self.variables = [dict(item) for item in variables]
        self.count.setText(str(len(self.variables)))
        self.table.setRowCount(0)

        for item in self.variables[:80]:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(
                row,
                0,
                QTableWidgetItem(str(item.get("name", ""))),
            )
            self.table.setItem(
                row,
                1,
                QTableWidgetItem(str(item.get("type", ""))),
            )
            value = item.get("value") or item.get("shape") or ""
            self.table.setItem(
                row,
                2,
                QTableWidgetItem(str(value)),
            )
