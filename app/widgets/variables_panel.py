from PySide6.QtWidgets import QFrame, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout


class VariablesPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("PanelCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        title = QLabel("Variables")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Nombre", "Tipo", "Forma", "Valor"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(False)
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
