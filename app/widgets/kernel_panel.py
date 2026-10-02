from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class KernelPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("PanelCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(9, 8, 9, 8)
        layout.setSpacing(4)

        header = QHBoxLayout()
        header.setSpacing(5)

        title = QLabel("Kernel")
        title.setObjectName("SectionTitle")

        self.state_badge = QLabel("detenido")
        self.state_badge.setObjectName("StateBadgeOff")

        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self.state_badge)
        layout.addLayout(header)

        self.kernel_name = QLabel("Python 3.x")
        self.kernel_name.setObjectName("KernelName")

        self.kernel_uptime = QLabel("Actividad: —")
        self.kernel_uptime.setObjectName("MutedLabel")

        layout.addWidget(self.kernel_name)
        layout.addWidget(self.kernel_uptime)

        self.restart_button = QPushButton("Reiniciar kernel")
        self.restart_button.setObjectName("SecondaryButton")
        layout.addWidget(self.restart_button)

    def update_info(self, kernel_name: str, state: str, uptime: str) -> None:
        self.kernel_name.setText(kernel_name)

        state_text = state or "desconocido"
        self.state_badge.setText(state_text)

        active = state_text.lower() not in {"detenido", "sin sesión", "dead", "-"}
        self.state_badge.setObjectName("StateBadgeOn" if active else "StateBadgeOff")
        self.state_badge.style().unpolish(self.state_badge)
        self.state_badge.style().polish(self.state_badge)

        self.kernel_uptime.setText(f"Actividad: {uptime}")
