from __future__ import annotations

import os
import time
from pathlib import Path

from PySide6.QtCore import QTimer, Qt, QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from .jupyter_manager import JupyterServerManager
from .theme import APP_STYLE
from .widgets.file_explorer import FileExplorerPanel
from .widgets.kernel_panel import KernelPanel
from .widgets.log_console import LogConsolePanel
from .widgets.mini_terminal import MiniTerminalPanel
from .widgets.variables_panel import VariablesPanel


class MainWindow(QMainWindow):
    def __init__(self, root_dir: str | None = None):
        super().__init__()

        self.root_dir = os.path.abspath(root_dir or os.getcwd())
        self.setWindowTitle("Archyter Desktop")
        self.resize(1600, 940)
        self.setMinimumSize(1100, 700)

        self.manager = JupyterServerManager(root_dir=self.root_dir)
        self.manager.log_line.connect(self._append_log)
        self.manager.status_changed.connect(self._update_status_text)

        self.app_start_time = time.time()
        self.active_kernel_id: str | None = None

        self._build_ui()
        self.setStyleSheet(APP_STYLE)
        self._start_jupyter()
        self._start_timers()

    def _build_ui(self) -> None:
        central = QWidget()
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(12)

        root_layout.addWidget(self._create_top_bar())

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._create_left_sidebar())
        splitter.addWidget(self._create_center_browser())
        splitter.addWidget(self._create_right_sidebar())
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        splitter.setSizes([270, 1040, 320])

        root_layout.addWidget(splitter, 1)
        root_layout.addWidget(self._create_status_bar())

        self.setCentralWidget(central)

    def _create_top_bar(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("TopBar")

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        back_btn = QPushButton("←")
        back_btn.setFixedWidth(42)
        back_btn.clicked.connect(self._go_home)
        layout.addWidget(back_btn)

        title = QLabel("Archyter Desktop")
        title.setObjectName("TitleLabel")
        layout.addWidget(title)
        layout.addStretch(1)

        self.new_button = QPushButton("Nuevo")
        self.new_button.clicked.connect(self._new_notebook)

        self.save_button = QPushButton("Guardar")
        self.save_button.clicked.connect(self._save_active_document)

        self.run_button = QPushButton("▶ Ejecutar")
        self.run_button.setObjectName("PrimaryButton")
        self.run_button.clicked.connect(self._run_active_cell)

        self.kernel_button = QPushButton("Kernel")
        self.kernel_button.clicked.connect(self._restart_active_kernel)

        self.terminal_button = QPushButton("Terminal")
        self.terminal_button.clicked.connect(self._focus_terminal)

        self.settings_button = QPushButton("Ajustes")
        self.settings_button.clicked.connect(self._choose_project_root)

        for button in (
            self.new_button,
            self.save_button,
            self.run_button,
            self.kernel_button,
            self.terminal_button,
            self.settings_button,
        ):
            layout.addWidget(button)

        return frame

    def _create_left_sidebar(self) -> QWidget:
        self.file_explorer = FileExplorerPanel(self.root_dir)
        self.file_explorer.setMinimumWidth(235)
        self.file_explorer.setMaximumWidth(330)
        self.file_explorer.file_open_requested.connect(self._open_path)
        return self.file_explorer

    def _create_center_browser(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("CenterFrame")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 8, 8, 8)

        self.browser = QWebEngineView()
        self.browser.setZoomFactor(1.0)
        self.browser.setStyleSheet("background: #0b1220; border: none;")
        self.browser.loadFinished.connect(self._on_page_loaded)
        layout.addWidget(self.browser, 1)

        return frame

    def _create_right_sidebar(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("RightSidebar")
        frame.setMinimumWidth(290)
        frame.setMaximumWidth(370)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.kernel_panel = KernelPanel()
        self.kernel_panel.restart_button.clicked.connect(self._restart_active_kernel)

        self.variables_panel = VariablesPanel()
        self.log_panel = LogConsolePanel()
        self.terminal_panel = MiniTerminalPanel(self.root_dir)
        self.terminal_panel.setMinimumHeight(210)

        layout.addWidget(self.kernel_panel)
        layout.addWidget(self.variables_panel, 1)
        layout.addWidget(self.log_panel, 1)
        layout.addWidget(self.terminal_panel, 1)

        return frame

    def _create_status_bar(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("StatusBarFrame")

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 10, 16, 10)

        self.left_status = QLabel(f"Proyecto: {Path(self.root_dir).name}")
        self.right_status = QLabel("Python 3 | Kernel detenido | UTF-8 | Archyter Desktop")
        self.right_status.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        layout.addWidget(self.left_status)
        layout.addStretch(1)
        layout.addWidget(self.right_status)

        return frame

    def _start_jupyter(self) -> None:
        try:
            self.manager.start()
            self.browser.setUrl(QUrl(self.manager.open_url_for_path()))
            self._append_log("JupyterLab iniciado correctamente.")
        except Exception as exc:
            QMessageBox.critical(self, "Error al iniciar Jupyter", str(exc))
            self._append_log(f"ERROR: {exc}")

    def _start_timers(self) -> None:
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._refresh_server_state)
        self.refresh_timer.start(4000)

    def _on_page_loaded(self, ok: bool) -> None:
        if not ok:
            return

        self.manager.inject_shortcuts(self.browser.page())

        QTimer.singleShot(
            700,
            lambda: self.browser.page().runJavaScript(
                "window.__archyter && window.__archyter.refit && window.__archyter.refit();"
            ),
        )

    def _append_log(self, text: str) -> None:
        self.log_panel.append_line(text)

    def _update_status_text(self, state: str) -> None:
        self.right_status.setText(
            f"Python 3 | Kernel {state} | UTF-8 | Archyter Desktop"
        )

    def _refresh_server_state(self) -> None:
        try:
            session = self.manager.active_session()

            if not session:
                self.active_kernel_id = None
                self.kernel_panel.update_info(
                    "Python 3.x (sin sesión)",
                    "sin sesión",
                    "-",
                )
                self.variables_panel.set_variables([])
                return

            kernel = session.get("kernel", {})
            kernel_name = kernel.get("name", "python")
            kernel_id = kernel.get("id")
            execution_state = kernel.get("execution_state", "activo")

            self.active_kernel_id = kernel_id

            uptime_seconds = int(time.time() - self.app_start_time)
            uptime_text = f"{uptime_seconds // 60} min {uptime_seconds % 60}s"

            display_kernel = kernel_name
            if "julia" in kernel_name.lower():
                display_kernel = kernel_name
            elif "python" in kernel_name.lower():
                display_kernel = f"{kernel_name} (ipykernel)"

            self.kernel_panel.update_info(
                display_kernel,
                execution_state,
                uptime_text,
            )

            self.right_status.setText(
                f"{kernel_name} | Kernel conectado | UTF-8 | Archyter Desktop"
            )

            self.left_status.setText(
                f'Proyecto: {Path(self.root_dir).name} | Notebook: {session.get("path", "-")}'
            )

            if kernel_id:
                try:
                    variables = self.manager.variable_snapshot(
                        kernel_id,
                        kernel_name=kernel_name,
                        timeout=3.0,
                    )
                except Exception as exc:
                    variables = [
                        {
                            "name": "info",
                            "type": "estado",
                            "shape": "-",
                            "value": "Ejecuta una celda para actualizar variables.",
                        }
                    ]
                    self._append_log(f"Variables: {exc}")

                self.variables_panel.set_variables(variables)

        except Exception as exc:
            self._append_log(f"Refresh: {exc}")

    def _go_home(self) -> None:
        self.browser.setUrl(QUrl(self.manager.open_url_for_path()))

    def _open_path(self, path: str) -> None:
        self.browser.setUrl(QUrl(self.manager.open_url_for_path(path)))

    def _new_notebook(self) -> None:
        try:
            path = self.manager.create_notebook(self.root_dir)
            self._append_log(f"Notebook creado: {path}")
            self._open_path(path)
        except Exception as exc:
            QMessageBox.warning(
                self,
                "No se pudo crear el notebook",
                str(exc),
            )

    def _save_active_document(self) -> None:
        self.browser.page().runJavaScript(
            "window.__archyter && window.__archyter.save && window.__archyter.save();"
        )
        self._append_log("Guardar enviado al notebook activo.")

    def _run_active_cell(self) -> None:
        self.browser.page().runJavaScript(
            "window.__archyter && window.__archyter.runCell && window.__archyter.runCell();"
        )
        self._append_log("Ejecutar celda enviado al notebook activo.")

    def _restart_active_kernel(self) -> None:
        if not self.active_kernel_id:
            QMessageBox.information(
                self,
                "Kernel",
                "No hay un kernel activo todavía.",
            )
            return

        try:
            self.manager.restart_kernel(self.active_kernel_id)
            self._append_log("Kernel reiniciado.")
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Kernel",
                f"No se pudo reiniciar: {exc}",
            )

    def _focus_terminal(self) -> None:
        self.terminal_panel.input.setFocus()

    def _choose_project_root(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self,
            "Selecciona una carpeta de proyecto",
            self.root_dir,
        )

        if not folder:
            return

        QMessageBox.information(
            self,
            "Carpeta de proyecto",
            "En esta primera versión el cambio de raíz se aplica al reiniciar.\n\n"
            f"Carpeta elegida: {folder}",
        )

    def closeEvent(self, event) -> None:
        self.manager.shutdown()
        super().closeEvent(event)
