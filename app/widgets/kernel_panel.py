from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout


class KernelPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("PanelCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        title = QLabel("Kernel")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        self.kernel_name = QLabel("Python 3.x (sin sesión)")
        self.kernel_state = QLabel("Estado: detenido")
        self.kernel_uptime = QLabel("Tiempo de actividad: -")

        layout.addWidget(self.kernel_name)
        layout.addWidget(self.kernel_state)
        layout.addWidget(self.kernel_uptime)

        self.restart_button = QPushButton("Reiniciar kernel")
        layout.addWidget(self.restart_button)

    def update_info(self, kernel_name: str, state: str, uptime: str) -> None:
        self.kernel_name.setText(kernel_name)
        self.kernel_state.setText(f"Estado: {state}")
        self.kernel_uptime.setText(f"Tiempo de actividad: {uptime}")
