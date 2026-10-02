from __future__ import annotations

import os
import time
from pathlib import Path

from send2trash import send2trash
from PySide6.QtCore import QSettings, QTimer, Qt, QUrl
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QFrame,
    QHeaderView,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .icons import app_icon, themed_icon
from .jupyter_manager import JupyterServerManager
from .theme import APP_STYLE
from .widgets.file_explorer import FileExplorerPanel
from .widgets.kernel_panel import KernelPanel
from .widgets.log_console import LogConsolePanel
from .widgets.mini_terminal import MiniTerminalPanel
from .widgets.variables_panel import VariablesPanel


class QuietWebEnginePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, line_number, source_id):
        if "No active debugger session" in message:
            return
        super().javaScriptConsoleMessage(level, message, line_number, source_id)


class MainWindow(QMainWindow):
    def __init__(self, root_dir: str | None = None):
        super().__init__()

        self.root_dir = os.path.abspath(root_dir or os.getcwd())
        self.settings = QSettings("EduardoMedinaLabs", "ArchyterDesktop")
        self.settings.setValue("last_project", self.root_dir)
        self.setWindowTitle("Archyter Desktop")
        self.setWindowIcon(app_icon())

        screen = QApplication.primaryScreen()
        available = screen.availableGeometry() if screen else None
        self.compact_mode = bool(
            available
            and (
                available.width() <= 1400
                or available.height() <= 820
            )
        )

        if self.compact_mode and available:
            self.resize(
                min(available.width(), 1366),
                min(available.height(), 780),
            )
            self.setMinimumSize(960, 620)
        else:
            self.resize(1600, 940)
            self.setMinimumSize(1100, 700)

        self.manager = JupyterServerManager(root_dir=self.root_dir)

        self.app_start_time = time.time()
        self.active_kernel_id: str | None = None
        self.active_kernel_name: str = ""
        self.active_document_path: str | None = None
        self._popout_dialogs: list[QDialog] = []
        self._page_retry_count = 0

        self._build_ui()
        self.setStyleSheet(APP_STYLE)
        self._connect_manager(self.manager)
        self._start_jupyter()
        self._start_timers()

    def _build_ui(self) -> None:
        central = QWidget()
        root_layout = QVBoxLayout(central)

        if self.compact_mode:
            root_layout.setContentsMargins(7, 7, 7, 7)
            root_layout.setSpacing(6)
        else:
            root_layout.setContentsMargins(16, 16, 16, 16)
            root_layout.setSpacing(12)

        root_layout.addWidget(self._create_top_bar())

        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.setHandleWidth(3 if self.compact_mode else 5)

        self.main_splitter.addWidget(self._create_left_sidebar())
        self.main_splitter.addWidget(self._create_center_browser())
        self.main_splitter.addWidget(self._create_right_sidebar())

        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 1)
        self.main_splitter.setStretchFactor(2, 0)

        if self.compact_mode:
            self.main_splitter.setSizes([205, 905, 220])
        else:
            self.main_splitter.setSizes([250, 1080, 280])

        root_layout.addWidget(self.main_splitter, 1)
        root_layout.addWidget(self._create_status_bar())

        self.setCentralWidget(central)

    def _create_top_bar(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("TopBar")
        frame.setFixedHeight(52 if self.compact_mode else 66)

        layout = QHBoxLayout(frame)

        if self.compact_mode:
            layout.setContentsMargins(10, 6, 10, 6)
            layout.setSpacing(6)
        else:
            layout.setContentsMargins(16, 12, 16, 12)
            layout.setSpacing(10)

        back_btn = QPushButton()
        back_btn.setObjectName("BackButton")
        back_btn.setIcon(
            themed_icon(
                "go-previous",
                QStyle.StandardPixmap.SP_ArrowBack,
            )
        )
        back_btn.setToolTip("Volver al inicio del proyecto")
        back_btn.setFixedWidth(32 if self.compact_mode else 42)
        back_btn.clicked.connect(self._go_home)
        layout.addWidget(back_btn)

        icon_label = QLabel()
        icon_label.setObjectName("AppIcon")
        icon_label.setPixmap(
            app_icon().pixmap(24, 24)
        )
        icon_label.setFixedSize(28, 28)
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        title = QLabel("Archyter Desktop")
        title.setObjectName("TitleLabel")
        layout.addWidget(title)
        layout.addStretch(1)

        self.new_button = QToolButton()
        self.new_button.setObjectName("ToolbarMenuButton")
        self.new_button.setText("Nuevo")
        self.new_button.setIcon(
            themed_icon(
                "document-new",
                QStyle.StandardPixmap.SP_FileDialogNewFolder,
            )
        )
        self.new_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.new_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        new_menu = QMenu(self.new_button)
        notebook_action = new_menu.addAction(
            themed_icon("application-x-ipynb"),
            "Notebook",
        )
        folder_action = new_menu.addAction(
            themed_icon(
                "folder-new",
                QStyle.StandardPixmap.SP_FileDialogNewFolder,
            ),
            "Carpeta",
        )
        file_action = new_menu.addAction(
            themed_icon("text-x-generic"),
            "Archivo de texto",
        )

        notebook_action.triggered.connect(self._new_notebook)
        folder_action.triggered.connect(self._new_folder)
        file_action.triggered.connect(self._new_text_file)
        self.new_button.setMenu(new_menu)

        self.save_button = QPushButton("Guardar")
        self.save_button.setIcon(
            themed_icon(
                "document-save",
                QStyle.StandardPixmap.SP_DialogSaveButton,
            )
        )
        self.save_button.clicked.connect(self._save_active_document)

        self.run_button = QPushButton("Ejecutar")
        self.run_button.setObjectName("PrimaryButton")
        self.run_button.setIcon(
            themed_icon(
                "media-playback-start",
                QStyle.StandardPixmap.SP_MediaPlay,
            )
        )
        self.run_button.clicked.connect(self._run_active_cell)

        self.kernel_button = QPushButton("Kernel")
        self.kernel_button.setIcon(
            themed_icon(
                "view-refresh",
                QStyle.StandardPixmap.SP_BrowserReload,
            )
        )
        self.kernel_button.setToolTip("Reiniciar el kernel activo")
        self.kernel_button.clicked.connect(self._restart_active_kernel)

        self.terminal_button = QPushButton("Terminal")
        self.terminal_button.setIcon(
            themed_icon(
                "utilities-terminal",
                QStyle.StandardPixmap.SP_ComputerIcon,
            )
        )
        self.terminal_button.setToolTip("Abrir terminal grande")
        self.terminal_button.clicked.connect(self._show_terminal_dialog)

        self.settings_button = QPushButton("Proyecto")
        self.settings_button.setIcon(
            themed_icon(
                "folder-open",
                QStyle.StandardPixmap.SP_DirOpenIcon,
            )
        )
        self.settings_button.setToolTip("Cambiar la carpeta raíz del proyecto")
        self.settings_button.clicked.connect(self._choose_project_root)

        buttons = (
            self.new_button,
            self.save_button,
            self.run_button,
            self.kernel_button,
            self.terminal_button,
            self.settings_button,
        )

        if self.compact_mode:
            for button in buttons:
                button.setFixedHeight(32)

        for button in buttons:
            layout.addWidget(button)

        return frame

    def _create_left_sidebar(self) -> QWidget:
        self.file_explorer = FileExplorerPanel(self.root_dir)

        if self.compact_mode:
            self.file_explorer.setMinimumWidth(185)
            self.file_explorer.setMaximumWidth(245)
        else:
            self.file_explorer.setMinimumWidth(225)
            self.file_explorer.setMaximumWidth(310)

        self.file_explorer.file_open_requested.connect(self._open_path)
        self.file_explorer.new_requested.connect(self._handle_new_requested)
        self.file_explorer.location_changed.connect(self._location_changed)
        self.file_explorer.delete_requested.connect(
            self._delete_path_from_explorer
        )
        return self.file_explorer

    def _create_center_browser(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("CenterFrame")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(
            5 if self.compact_mode else 8,
            5 if self.compact_mode else 8,
            5 if self.compact_mode else 8,
            5 if self.compact_mode else 8,
        )
        layout.setSpacing(5)

        document_bar = QFrame()
        document_bar.setObjectName("DocumentBar")
        document_bar.setFixedHeight(30 if self.compact_mode else 34)

        document_layout = QHBoxLayout(document_bar)
        document_layout.setContentsMargins(8, 2, 8, 2)
        document_layout.setSpacing(6)

        self.document_icon = QLabel()
        self.document_icon.setPixmap(
            themed_icon(
                "application-x-ipynb",
                QStyle.StandardPixmap.SP_FileIcon,
            ).pixmap(16, 16)
        )
        self.document_icon.setFixedSize(18, 18)

        self.document_label = QLabel("Inicio del proyecto")
        self.document_label.setObjectName("ActiveDocumentLabel")

        self.document_location = QLabel(Path(self.root_dir).name)
        self.document_location.setObjectName("MutedLabel")
        self.document_location.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        document_layout.addWidget(self.document_icon)
        document_layout.addWidget(self.document_label)
        document_layout.addStretch(1)
        document_layout.addWidget(self.document_location)

        layout.addWidget(document_bar)

        self.browser = QWebEngineView()
        self.browser.setPage(QuietWebEnginePage(self.browser))
        self.browser.setZoomFactor(0.88 if self.compact_mode else 1.0)
        self.browser.setStyleSheet("background: #ffffff; border: none;")
        self.browser.loadFinished.connect(self._on_page_loaded)
        layout.addWidget(self.browser, 1)

        return frame

    def _create_right_sidebar(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("RightSidebar")

        if self.compact_mode:
            frame.setMinimumWidth(205)
            frame.setMaximumWidth(250)
        else:
            frame.setMinimumWidth(250)
            frame.setMaximumWidth(310)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(7, 7, 7, 7)
        layout.setSpacing(6)

        heading = QHBoxLayout()
        title = QLabel("Inspector")
        title.setObjectName("SectionTitle")
        subtitle = QLabel("sesión")
        subtitle.setObjectName("MutedLabel")
        heading.addWidget(title)
        heading.addStretch(1)
        heading.addWidget(subtitle)
        layout.addLayout(heading)

        self.kernel_panel = KernelPanel()
        self.kernel_panel.restart_button.clicked.connect(self._restart_active_kernel)

        self.variables_panel = VariablesPanel()
        self.variables_panel.refresh_requested.connect(self._refresh_variables)
        self.variables_panel.expand_requested.connect(self._show_variables_dialog)

        self.log_panel = LogConsolePanel()
        self.log_panel.expand_requested.connect(self._show_logs_dialog)

        self.terminal_panel = MiniTerminalPanel(self.root_dir)
        self.terminal_panel.expand_requested.connect(self._show_terminal_dialog)

        if self.compact_mode:
            self.kernel_panel.setMinimumHeight(102)
            self.kernel_panel.setMaximumHeight(116)

            self.variables_panel.setMinimumHeight(128)
            self.variables_panel.setMaximumHeight(160)

            self.log_panel.setMinimumHeight(92)
            self.log_panel.setMaximumHeight(120)

            self.terminal_panel.setMinimumHeight(125)
            self.terminal_panel.setMaximumHeight(155)
        else:
            self.kernel_panel.setMaximumHeight(130)
            self.variables_panel.setMinimumHeight(155)
            self.log_panel.setMinimumHeight(120)
            self.terminal_panel.setMinimumHeight(170)

        layout.addWidget(self.kernel_panel)
        layout.addWidget(self.variables_panel)
        layout.addWidget(self.log_panel)
        layout.addWidget(self.terminal_panel)
        layout.addStretch(1)

        return frame

    def _create_status_bar(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("StatusBarFrame")
        frame.setFixedHeight(30 if self.compact_mode else 40)

        layout = QHBoxLayout(frame)

        if self.compact_mode:
            layout.setContentsMargins(10, 3, 10, 3)
            layout.setSpacing(8)
        else:
            layout.setContentsMargins(16, 10, 16, 10)

        self.left_status = QLabel(f"Proyecto: {Path(self.root_dir).name}")
        self.right_status = QLabel(
            "Python 3 | Kernel detenido | UTF-8 | Archyter Desktop"
        )
        self.right_status.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        layout.addWidget(self.left_status)
        layout.addStretch(1)
        layout.addWidget(self.right_status)

        return frame

    def _connect_manager(self, manager: JupyterServerManager) -> None:
        manager.log_line.connect(self._append_log)
        manager.status_changed.connect(self._update_status_text)

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
            if self._page_retry_count < 2:
                self._page_retry_count += 1
                self._append_log(
                    f"JupyterLab no respondió; reintento {self._page_retry_count}/2."
                )
                QTimer.singleShot(700, self.browser.reload)
                return

            self._append_log("No se pudo cargar la vista de JupyterLab.")
            self.left_status.setText("Error al cargar JupyterLab")
            return

        self._page_retry_count = 0
        self.manager.inject_shortcuts(
            self.browser.page(),
            compact=self.compact_mode,
        )

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
                    "Python 3.x",
                    "sin sesión",
                    "-",
                )
                self.variables_panel.set_variables([])
                return

            kernel = session.get("kernel", {})
            kernel_name = kernel.get("name", "python")
            kernel_id = kernel.get("id")
            execution_state = kernel.get("execution_state", "activo")

            kernel_changed = kernel_id != self.active_kernel_id
            self.active_kernel_id = kernel_id
            self.active_kernel_name = kernel_name

            if kernel_changed:
                self.variables_panel.set_variables([])

            uptime_seconds = int(time.time() - self.app_start_time)
            uptime_text = f"{uptime_seconds // 60}m {uptime_seconds % 60}s"

            display_kernel = kernel_name
            if "python" in kernel_name.lower():
                display_kernel = kernel_name

            self.kernel_panel.update_info(
                display_kernel,
                execution_state,
                uptime_text,
            )

            self.right_status.setText(
                f"{kernel_name} | conectado | UTF-8 | Archyter"
            )

            session_path = session.get("path", "")
            notebook_name = Path(session_path or "-").name
            self.left_status.setText(
                f"{Path(self.root_dir).name}  •  {notebook_name}"
            )

            if session_path:
                absolute = os.path.abspath(
                    os.path.join(self.root_dir, session_path)
                )
                if (
                    os.path.exists(absolute)
                    and absolute != self.active_document_path
                ):
                    self.file_explorer.set_active_path(absolute)
                    self._set_active_document(absolute)

        except Exception as exc:
            self._append_log(f"Refresh: {exc}")

    def _refresh_variables(self) -> None:
        if not self.active_kernel_id:
            self.variables_panel.set_variables([])
            return

        self.variables_panel.set_refreshing(True)
        try:
            variables = self.manager.variable_snapshot(
                self.active_kernel_id,
                kernel_name=self.active_kernel_name,
                timeout=5.0,
            )
            self.variables_panel.set_variables(variables)
        except Exception as exc:
            self._append_log(f"Variables: {exc}")
        finally:
            self.variables_panel.set_refreshing(False)

    def _register_popout(self, dialog: QDialog) -> None:
        self._popout_dialogs.append(dialog)

        def cleanup(*_args) -> None:
            if dialog in self._popout_dialogs:
                self._popout_dialogs.remove(dialog)

        dialog.destroyed.connect(cleanup)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def _prepare_popout(self, title: str) -> QDialog:
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setAttribute(Qt.WA_DeleteOnClose, True)
        dialog.setStyleSheet(APP_STYLE)

        screen = QApplication.primaryScreen()
        available = screen.availableGeometry() if screen else None

        if available:
            width = min(980, max(720, int(available.width() * 0.72)))
            height = min(620, max(480, int(available.height() * 0.72)))
            dialog.resize(width, height)
        else:
            dialog.resize(900, 580)

        return dialog

    def _show_variables_dialog(self) -> None:
        dialog = self._prepare_popout("Archyter — Variables")
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel("Variables del kernel")
        title.setObjectName("TitleLabel")

        refresh = QPushButton("↻ Actualizar")
        refresh.setObjectName("PrimaryButton")

        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(refresh)
        layout.addLayout(header)

        table = QTableWidget(0, 4)
        table.setHorizontalHeaderLabels(["Nombre", "Tipo", "Forma", "Valor"])
        table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch
        )
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        layout.addWidget(table, 1)

        def populate() -> None:
            table.setRowCount(0)
            for item in self.variables_panel.variables:
                row = table.rowCount()
                table.insertRow(row)
                table.setItem(row, 0, QTableWidgetItem(str(item.get("name", ""))))
                table.setItem(row, 1, QTableWidgetItem(str(item.get("type", ""))))
                table.setItem(row, 2, QTableWidgetItem(str(item.get("shape", ""))))
                table.setItem(row, 3, QTableWidgetItem(str(item.get("value", ""))))

        def refresh_all() -> None:
            refresh.setEnabled(False)
            refresh.setText("Actualizando…")
            QApplication.processEvents()
            self._refresh_variables()
            populate()
            refresh.setText("↻ Actualizar")
            refresh.setEnabled(True)

        refresh.clicked.connect(refresh_all)
        populate()
        self._register_popout(dialog)

    def _show_logs_dialog(self) -> None:
        dialog = self._prepare_popout("Archyter — Consola / logs")
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title = QLabel("Consola del kernel / logs")
        title.setObjectName("TitleLabel")
        layout.addWidget(title)

        console = QPlainTextEdit()
        console.setObjectName("LogDialog")
        console.setReadOnly(True)
        console.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        console.setPlainText(self.log_panel.all_text())
        layout.addWidget(console, 1)

        self.manager.log_line.connect(console.appendPlainText)

        def disconnect_live_log(*_args) -> None:
            try:
                self.manager.log_line.disconnect(console.appendPlainText)
            except (RuntimeError, TypeError):
                pass

        dialog.destroyed.connect(disconnect_live_log)
        self._register_popout(dialog)

    def _show_terminal_dialog(self) -> None:
        dialog = self._prepare_popout("Archyter — Terminal")
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(10, 10, 10, 10)

        terminal = MiniTerminalPanel(self.root_dir)
        if hasattr(terminal, "title_button"):
            terminal.title_button.hide()

        layout.addWidget(terminal, 1)
        dialog.finished.connect(lambda _code: terminal.shutdown())
        self._register_popout(dialog)

    def _set_active_document(self, path: str | None) -> None:
        if not path:
            self.active_document_path = None
            self.document_label.setText("Inicio del proyecto")
            self.document_location.setText(Path(self.root_dir).name)
            return

        absolute = os.path.abspath(path)
        self.active_document_path = absolute
        self.document_label.setText(Path(absolute).name)

        try:
            parent = Path(absolute).parent.relative_to(self.root_dir)
            location = (
                Path(self.root_dir).name
                if str(parent) == "."
                else f"{Path(self.root_dir).name} / {parent.as_posix()}"
            )
        except ValueError:
            location = str(Path(absolute).parent)

        self.document_location.setText(location)
        self.document_location.setToolTip(str(Path(absolute).parent))

    def _location_changed(self, directory: str) -> None:
        try:
            relative = Path(directory).relative_to(self.root_dir)
            label = (
                Path(self.root_dir).name
                if str(relative) == "."
                else f"{Path(self.root_dir).name} / {relative.as_posix()}"
            )
        except ValueError:
            label = directory

        self._set_status_text(f"Nuevo se creará en: {label}")

    def _set_status_text(self, text: str) -> None:
        self.left_status.setText(text)

    def _handle_new_requested(self, kind: str) -> None:
        if kind == "notebook":
            self._new_notebook()
        elif kind == "folder":
            self._new_folder()
        elif kind == "file":
            self._new_text_file()

    def _current_creation_directory(self) -> str:
        if hasattr(self, "file_explorer"):
            return self.file_explorer.current_directory()
        return self.root_dir

    def _go_home(self) -> None:
        self._set_active_document(None)
        self.browser.setUrl(QUrl(self.manager.open_url_for_path()))

    def _open_path(self, path: str) -> None:
        self.file_explorer.set_active_path(path)
        self._set_active_document(path)
        self.browser.setUrl(QUrl(self.manager.open_url_for_path(path)))

    def _delete_path_from_explorer(self, path: str) -> None:
        target = Path(path).expanduser().resolve()

        try:
            target.relative_to(Path(self.root_dir).resolve())
        except ValueError:
            QMessageBox.warning(
                self,
                "No se puede eliminar",
                "El archivo está fuera del proyecto activo.",
            )
            return

        if not target.is_file():
            QMessageBox.information(
                self,
                "Archivo no disponible",
                "El archivo ya no existe o no es un archivo normal.",
            )
            self.file_explorer.refresh()
            return

        answer = QMessageBox.question(
            self,
            "Enviar a la papelera",
            (
                f"¿Quieres enviar a la papelera este archivo?\n\n"
                f"{target.name}\n\n"
                "Podrás recuperarlo desde la papelera del sistema."
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            send2trash(str(target))
        except Exception as exc:
            QMessageBox.critical(
                self,
                "No se pudo eliminar",
                f"No pude enviar el archivo a la papelera.\n\n{exc}",
            )
            return

        was_active = (
            self.active_document_path is not None
            and Path(self.active_document_path).resolve() == target
        )

        self.file_explorer.refresh()

        if was_active:
            self._go_home()

        self._append_log(f"Archivo enviado a la papelera: {target}")
        self._set_status_text(f"Enviado a la papelera: {target.name}")

    def _new_notebook(self) -> None:
        directory = self._current_creation_directory()

        try:
            path = self.manager.create_notebook(directory)
            self.file_explorer.refresh()
            self.file_explorer.set_active_path(path)
            self._append_log(f"Notebook creado: {path}")
            self._open_path(path)
        except Exception as exc:
            QMessageBox.warning(
                self,
                "No se pudo crear el notebook",
                str(exc),
            )

    def _new_folder(self) -> None:
        directory = Path(self._current_creation_directory())

        name, ok = QInputDialog.getText(
            self,
            "Nueva carpeta",
            "Nombre de la carpeta:",
        )
        name = name.strip()

        if not ok or not name:
            return

        if "/" in name or "\\" in name or name in {".", ".."}:
            QMessageBox.warning(
                self,
                "Nombre no válido",
                "Usa un nombre de carpeta simple, sin rutas.",
            )
            return

        destination = directory / name

        try:
            destination.mkdir()
            self.file_explorer.refresh()
            self._append_log(f"Carpeta creada: {destination}")
            self._set_status_text(f"Carpeta creada: {name}")
        except FileExistsError:
            QMessageBox.information(
                self,
                "La carpeta ya existe",
                f"Ya existe una carpeta llamada {name}.",
            )
        except Exception as exc:
            QMessageBox.warning(
                self,
                "No se pudo crear la carpeta",
                str(exc),
            )

    def _new_text_file(self) -> None:
        directory = Path(self._current_creation_directory())

        name, ok = QInputDialog.getText(
            self,
            "Nuevo archivo",
            "Nombre del archivo:",
            text="notas.txt",
        )
        name = name.strip()

        if not ok or not name:
            return

        if "/" in name or "\\" in name or name in {".", ".."}:
            QMessageBox.warning(
                self,
                "Nombre no válido",
                "Usa un nombre de archivo simple, sin rutas.",
            )
            return

        destination = directory / name

        if destination.exists():
            QMessageBox.information(
                self,
                "El archivo ya existe",
                f"Ya existe {name} en esa carpeta.",
            )
            return

        try:
            destination.write_text("", encoding="utf-8")
            self.file_explorer.refresh()
            self.file_explorer.set_active_path(str(destination))
            self._append_log(f"Archivo creado: {destination}")

            if destination.suffix.lower() in {
                ".txt",
                ".md",
                ".py",
                ".jl",
                ".json",
                ".yaml",
                ".yml",
                ".csv",
            }:
                self._open_path(str(destination))
        except Exception as exc:
            QMessageBox.warning(
                self,
                "No se pudo crear el archivo",
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

    def _choose_project_root(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self,
            "Selecciona una carpeta de proyecto",
            self.root_dir,
            QFileDialog.Option.ShowDirsOnly
            | QFileDialog.Option.DontUseNativeDialog,
        )

        if not folder:
            return

        new_root = os.path.abspath(folder)
        if new_root == self.root_dir:
            return

        self._switch_project_root(new_root)

    def _switch_project_root(self, new_root: str) -> None:
        self.left_status.setText("Cambiando proyecto…")
        QApplication.processEvents()

        try:
            self.manager.shutdown()
        except Exception as exc:
            self._append_log(f"Cierre del servidor anterior: {exc}")

        self.root_dir = os.path.abspath(new_root)
        self.settings.setValue("last_project", self.root_dir)
        self.active_kernel_id = None
        self.active_kernel_name = ""
        self.active_document_path = None

        self.file_explorer.set_root(self.root_dir)
        self._set_active_document(None)
        self.variables_panel.set_variables([])
        self.terminal_panel.set_working_directory(self.root_dir)

        self.manager = JupyterServerManager(root_dir=self.root_dir)
        self._connect_manager(self.manager)

        self.browser.setHtml(
            "<html><body style='font-family:sans-serif;padding:28px;"
            "color:#64748b;background:#fff'>"
            "<h3>Abriendo proyecto…</h3>"
            "<p>Iniciando JupyterLab en la nueva carpeta.</p>"
            "</body></html>"
        )

        try:
            self._start_jupyter()
            self.left_status.setText(
                f"Proyecto: {Path(self.root_dir).name}"
            )
            self._append_log(
                f"Proyecto activo: {self.root_dir}"
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "No se pudo abrir el proyecto",
                str(exc),
            )

    def closeEvent(self, event) -> None:
        if hasattr(self, "refresh_timer"):
            self.refresh_timer.stop()

        for dialog in list(self._popout_dialogs):
            dialog.close()

        if hasattr(self, "terminal_panel"):
            self.terminal_panel.shutdown()

        self.manager.shutdown()
        super().closeEvent(event)
