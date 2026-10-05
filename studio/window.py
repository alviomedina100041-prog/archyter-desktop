from __future__ import annotations

import os
import sys
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
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .animated import AnimatedPushButton, AnimatedToolButton, add_soft_shadow
from .explorer import ExplorerPanel
from .icons import app_icon, icon
from .inspector import InspectorPanel
from .jupyter_manager import JupyterManager
from .terminal import TerminalCard
from .theme import APP_STYLE
from .windows_chrome import apply_light_titlebar


class StudioWebPage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, line_number, source_id):
        ignored = (
            "No active debugger session",
            "ResizeObserver loop",
        )
        if any(fragment in message for fragment in ignored):
            return
        super().javaScriptConsoleMessage(level, message, line_number, source_id)


class StudioWindow(QMainWindow):
    def __init__(self, root_dir: str):
        super().__init__()
        self.root_dir = str(Path(root_dir).resolve())
        self.settings = QSettings("EduardoMedinaLabs", "ArchyterStudio")
        self.settings.setValue("last_project", self.root_dir)

        self.manager = JupyterManager(self.root_dir)
        self.active_document: str | None = None
        self.active_kernel_id: str | None = None
        self.active_kernel_name = ""
        self.started_at = time.time()
        self._page_retries = 0
        self._logs: list[str] = []

        self.setWindowTitle("Archyter Studio")
        self.setWindowIcon(app_icon())
        self.resize(1480, 900)
        self.setMinimumSize(1120, 700)

        self._build_ui()
        self.setStyleSheet(APP_STYLE)
        self._wire_manager()
        self._start_jupyter()
        self._start_timers()

    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(7)

        root.addWidget(self._build_topbar())

        content = QHBoxLayout()
        content.setSpacing(0)
        content.addWidget(self._build_navrail())

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setHandleWidth(3)

        self.explorer = ExplorerPanel(self.root_dir)
        self.explorer.setMinimumWidth(240)
        self.explorer.setMaximumWidth(320)
        add_soft_shadow(self.explorer, blur=16, y_offset=2, alpha=18)
        self.explorer.file_open_requested.connect(self._open_file)
        self.explorer.project_requested.connect(self._switch_project)
        self.explorer.new_requested.connect(self._handle_new)
        self.explorer.delete_requested.connect(self._delete_file)
        self.explorer.location_changed.connect(self._on_location_changed)
        self.explorer.add_recent(self.root_dir)

        self.splitter.addWidget(self.explorer)
        self.splitter.addWidget(self._build_editor())

        self.inspector = InspectorPanel(self.root_dir)
        self.inspector.setMinimumWidth(300)
        self.inspector.setMaximumWidth(370)
        self.inspector.refresh_variables.connect(self._refresh_variables)
        self.inspector.restart_kernel.connect(self._restart_kernel)
        self.inspector.stop_kernel.connect(self._stop_kernel)
        self.inspector.kernel_menu_requested.connect(self._show_kernel_details)
        self.inspector.terminal_expand_requested.connect(
            self._open_terminal_window
        )
        self.splitter.addWidget(self.inspector)

        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setStretchFactor(2, 0)
        self.splitter.setSizes([255, 900, 320])

        content.addWidget(self.splitter, 1)
        root.addLayout(content, 1)
        root.addWidget(self._build_statusbar())
        self.setCentralWidget(central)

    def _build_topbar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("TopBar")
        bar.setFixedHeight(60)
        add_soft_shadow(bar, blur=18, y_offset=2, alpha=19)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 7, 12, 7)
        layout.setSpacing(7)

        logo = QLabel()
        logo.setPixmap(app_icon().pixmap(30, 30))
        logo.setFixedSize(34, 34)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo)

        title = QLabel("Archyter Studio")
        title.setObjectName("AppTitle")
        layout.addWidget(title)
        layout.addSpacing(18)

        self.new_button = AnimatedToolButton(base_icon=17, hover_icon=19)
        self.new_button.setText("Nuevo")
        self.new_button.setIcon(icon("add"))
        self.new_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.new_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        menu = QMenu(self.new_button)
        notebook = menu.addAction(icon("notebook"), "Notebook")
        folder = menu.addAction(icon("folder"), "Carpeta")
        text_file = menu.addAction("Archivo de texto")
        notebook.triggered.connect(lambda: self._handle_new("notebook"))
        folder.triggered.connect(lambda: self._handle_new("folder"))
        text_file.triggered.connect(lambda: self._handle_new("file"))
        self.new_button.setMenu(menu)
        layout.addWidget(self.new_button)

        self.save_button = AnimatedPushButton("Guardar")
        self.save_button.setIcon(icon("save"))
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self._save)
        layout.addWidget(self.save_button)

        self.run_button = AnimatedPushButton("Ejecutar")
        self.run_button.setObjectName("Primary")
        self.run_button.setIcon(icon("play", QStyle.StandardPixmap.SP_MediaPlay))
        self.run_button.setEnabled(False)
        self.run_button.clicked.connect(self._run_cell)
        layout.addWidget(self.run_button)

        self.kernel_button = AnimatedPushButton("Kernel")
        self.kernel_button.setIcon(icon("refresh"))
        self.kernel_button.setToolTip("Reiniciar el kernel activo")
        self.kernel_button.clicked.connect(self._restart_kernel)
        layout.addWidget(self.kernel_button)

        terminal = AnimatedPushButton("Terminal")
        terminal.setIcon(icon("terminal"))
        terminal.clicked.connect(self._focus_terminal)
        layout.addWidget(terminal)

        project = AnimatedPushButton("Proyecto")
        project.setIcon(icon("project"))
        project.clicked.connect(self._choose_project)
        layout.addWidget(project)

        layout.addStretch(1)

        search = AnimatedToolButton(base_icon=18, hover_icon=20)
        search.setObjectName("IconButton")
        search.setIcon(icon("search"))
        search.setToolTip("Buscar en el proyecto")
        search.clicked.connect(self._search_project)
        layout.addWidget(search)

        settings = AnimatedToolButton(base_icon=18, hover_icon=20)
        settings.setObjectName("IconButton")
        settings.setIcon(icon("settings"))
        settings.setToolTip("Configuración de Archyter Studio")
        settings.clicked.connect(self._show_settings)
        layout.addWidget(settings)

        return bar

    def _build_navrail(self) -> QFrame:
        rail = QFrame()
        rail.setObjectName("NavRail")
        rail.setFixedWidth(48)
        layout = QVBoxLayout(rail)
        layout.setContentsMargins(5, 7, 5, 7)
        layout.setSpacing(5)

        entries = [
            ("home", "Proyecto", True),
            ("search", "Buscar", False),
            ("git", "Control de versiones", False),
            ("run", "Ejecutar", False),
            ("grid", "Herramientas", False),
        ]

        for name, tooltip, active in entries:
            button = AnimatedToolButton(base_icon=20, hover_icon=22)
            button.setObjectName("NavButton")
            button.setIcon(icon(name))
            button.setIconSize(button.iconSize() * 1.15)
            button.setToolTip(tooltip)
            button.setProperty("active", active)
            if name == "home":
                button.clicked.connect(self._show_welcome)
            elif name == "search":
                button.clicked.connect(self._search_project)
            elif name == "git":
                button.clicked.connect(self._git_status)
            elif name == "run":
                button.clicked.connect(self._run_cell)
            elif name == "grid":
                button.clicked.connect(self._show_settings)
            layout.addWidget(button)

        layout.addStretch(1)
        return rail

    def _build_editor(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("EditorFrame")
        add_soft_shadow(frame, blur=18, y_offset=2, alpha=18)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(5)

        document = QFrame()
        document.setObjectName("DocumentBar")
        document.setFixedHeight(38)

        row = QHBoxLayout(document)
        row.setContentsMargins(5, 3, 8, 3)
        row.setSpacing(5)

        self.document_tab = QFrame()
        self.document_tab.setObjectName("DocumentTab")
        tab_layout = QHBoxLayout(self.document_tab)
        tab_layout.setContentsMargins(7, 2, 5, 2)
        tab_layout.setSpacing(5)

        self.document_icon = QLabel()
        self.document_icon.setPixmap(icon("notebook").pixmap(17, 17))
        self.document_icon.setFixedSize(19, 19)

        self.document_title = QLabel("Inicio")
        self.document_title.setObjectName("DocumentTitle")

        self.close_document_button = AnimatedToolButton(
            base_icon=12,
            hover_icon=14,
        )
        self.close_document_button.setObjectName("TabButton")
        self.close_document_button.setText("×")
        self.close_document_button.setToolTip("Cerrar vista")
        self.close_document_button.clicked.connect(self._show_welcome)

        tab_layout.addWidget(self.document_icon)
        tab_layout.addWidget(self.document_title)
        tab_layout.addWidget(self.close_document_button)
        row.addWidget(self.document_tab)

        add_tab = AnimatedToolButton(base_icon=15, hover_icon=17)
        add_tab.setObjectName("TabButton")
        add_tab.setIcon(icon("add"))
        add_tab.setToolTip("Nuevo notebook")
        add_tab.clicked.connect(lambda: self._handle_new("notebook"))
        row.addWidget(add_tab)

        row.addStretch(1)

        self.document_path = QLabel(Path(self.root_dir).name)
        self.document_path.setObjectName("Muted")
        self.document_path.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignVCenter
        )
        row.addWidget(self.document_path)

        layout.addWidget(document)

        self.browser = QWebEngineView()
        self.browser.setPage(StudioWebPage(self.browser))
        self.browser.setZoomFactor(0.96)
        self.browser.setStyleSheet(
            "background:#ffffff;border:none;border-radius:8px;"
        )
        self.browser.loadFinished.connect(self._page_loaded)
        layout.addWidget(self.browser, 1)

        return frame

    def _build_statusbar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("StatusBar")
        bar.setFixedHeight(31)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 3, 12, 3)
        layout.setSpacing(12)

        self.kernel_status = QLabel("Python | iniciando")
        self.kernel_status.setObjectName("Muted")
        self.save_status = QLabel("Preparando Jupyter…")
        self.save_status.setObjectName("StatusGood")
        self.project_status = QLabel(self.root_dir)
        self.project_status.setObjectName("Muted")
        self.project_status.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(self.kernel_status)
        layout.addWidget(self.save_status)
        layout.addStretch(1)
        layout.addWidget(QLabel("UTF-8"))
        layout.addWidget(QLabel("Jupyter"))
        layout.addWidget(self.project_status)
        return bar

    def _wire_manager(self) -> None:
        self.manager.log_line.connect(self._append_log)
        self.manager.status_changed.connect(self._manager_status)

    def _append_log(self, line: str) -> None:
        self._logs.append(line)
        if len(self._logs) > 600:
            self._logs = self._logs[-600:]

    def _manager_status(self, state: str) -> None:
        self.kernel_status.setText(f"Jupyter | {state}")

    def _start_jupyter(self) -> None:
        QApplication.processEvents()
        try:
            self.manager.start()
            self._show_welcome()
            self.save_status.setText("Listo")
        except Exception as exc:
            self.save_status.setText("Error al iniciar")
            QMessageBox.critical(self, "Archyter Studio", str(exc))

    def _start_timers(self) -> None:
        self.state_timer = QTimer(self)
        self.state_timer.timeout.connect(self._refresh_session)
        self.state_timer.start(3000)

        self.dirty_timer = QTimer(self)
        self.dirty_timer.timeout.connect(self._refresh_dirty_state)
        self.dirty_timer.start(1400)

    def _page_loaded(self, ok: bool) -> None:
        if not ok:
            if self._page_retries < 2:
                self._page_retries += 1
                QTimer.singleShot(700, self.browser.reload)
                return
            self.save_status.setText("No se pudo cargar el editor")
            return

        self._page_retries = 0
        if self.browser.url().scheme() not in {"http", "https"}:
            return
        self.manager.inject_shell(self.browser.page())
        QTimer.singleShot(500, lambda: self.browser.page().runJavaScript(
            "window.dispatchEvent(new Event('resize'));"
        ))

    def _refresh_session(self) -> None:
        if not self.active_document:
            self.active_kernel_id = None
            self.inspector.update_kernel(
                "Python 3",
                "sin sesión",
                "Abre un notebook para iniciar.",
            )
            return

        try:
            session = self.manager.active_session(self.active_document)
        except Exception:
            return

        if not session:
            self.active_kernel_id = None
            self.inspector.update_kernel("Python 3", "sin sesión", "Abre un notebook para iniciar.")
            return

        kernel = session.get("kernel") or {}
        self.active_kernel_id = kernel.get("id")
        self.active_kernel_name = kernel.get("name") or "python"
        state = kernel.get("execution_state") or "activo"
        minutes = int((time.time() - self.started_at) // 60)
        self.inspector.update_kernel(
            self.active_kernel_name,
            state,
            f"Actividad: {minutes} min · Jupyter local",
        )
        self.kernel_status.setText(f"{self.active_kernel_name} | {state}")

        session_path = session.get("path")
        if session_path:
            absolute = str(Path(self.root_dir, session_path).resolve())
            if os.path.exists(absolute) and absolute != self.active_document:
                self._set_active_document(absolute)
                self.explorer.set_active_path(absolute)

    def _refresh_dirty_state(self) -> None:
        if not self.active_document:
            return

        def update(value) -> None:
            self.save_status.setText("Cambios sin guardar" if value else "Guardado")

        self.browser.page().runJavaScript(
            "window.__archyterStudio ? window.__archyterStudio.dirty() : false",
            update,
        )

    def _set_active_document(self, path: str | None) -> None:
        self.active_document = os.path.abspath(path) if path else None
        has_document = bool(self.active_document)
        self.document_tab.setVisible(has_document)
        self.save_button.setEnabled(has_document)
        self.run_button.setEnabled(
            bool(self.active_document and self.active_document.lower().endswith(".ipynb"))
        )

        if not self.active_document:
            self.document_title.setText("Inicio")
            self.document_path.setText(Path(self.root_dir).name)
            return

        target = Path(self.active_document)
        self.document_title.setText(target.name)
        try:
            parent = target.parent.relative_to(Path(self.root_dir))
            breadcrumb = Path(self.root_dir).name
            if str(parent) != ".":
                breadcrumb += f" / {parent.as_posix()}"
        except ValueError:
            breadcrumb = str(target.parent)
        self.document_path.setText(breadcrumb)
        self.document_path.setToolTip(str(target.parent))

    def _open_file(self, path: str) -> None:
        try:
            url = self.manager.open_url(path)
        except Exception as exc:
            QMessageBox.warning(self, "Abrir archivo", str(exc))
            return

        self._set_active_document(path)
        self.explorer.set_active_path(path)
        self.browser.setUrl(QUrl(url))

    def _handle_new(self, kind: str) -> None:
        directory = self.explorer.current_directory()
        if kind == "notebook":
            self._new_notebook(directory)
        elif kind == "folder":
            self._new_folder(directory)
        else:
            self._new_text_file(directory)

    def _new_notebook(self, directory: str) -> None:
        try:
            created = self.manager.create_notebook(directory)
            self.explorer.refresh()
            self._open_file(created)
        except Exception as exc:
            QMessageBox.warning(self, "Nuevo notebook", str(exc))

    def _new_folder(self, directory: str) -> None:
        name, ok = QInputDialog.getText(self, "Nueva carpeta", "Nombre:")
        name = name.strip()
        if not ok or not name:
            return
        if any(token in name for token in ("/", "\\")) or name in {".", ".."}:
            QMessageBox.warning(self, "Nueva carpeta", "Usa un nombre simple, sin rutas.")
            return
        target = Path(directory, name)
        try:
            target.mkdir()
            self.explorer.refresh()
        except FileExistsError:
            QMessageBox.information(self, "Nueva carpeta", "Ya existe una carpeta con ese nombre.")
        except Exception as exc:
            QMessageBox.warning(self, "Nueva carpeta", str(exc))

    def _new_text_file(self, directory: str) -> None:
        name, ok = QInputDialog.getText(self, "Nuevo archivo", "Nombre:", text="notas.txt")
        name = name.strip()
        if not ok or not name:
            return
        if any(token in name for token in ("/", "\\")) or name in {".", ".."}:
            QMessageBox.warning(self, "Nuevo archivo", "Usa un nombre simple, sin rutas.")
            return
        target = Path(directory, name)
        if target.exists():
            QMessageBox.information(self, "Nuevo archivo", "Ya existe un archivo con ese nombre.")
            return
        try:
            target.write_text("", encoding="utf-8")
            self.explorer.refresh()
            self._open_file(str(target))
        except Exception as exc:
            QMessageBox.warning(self, "Nuevo archivo", str(exc))

    def _delete_file(self, path: str) -> None:
        target = Path(path).resolve()
        try:
            target.relative_to(Path(self.root_dir).resolve())
        except ValueError:
            QMessageBox.warning(self, "Eliminar", "El archivo está fuera del proyecto.")
            return

        if not target.is_file():
            self.explorer.refresh()
            return

        answer = QMessageBox.question(
            self,
            "Enviar a la papelera",
            f"¿Enviar «{target.name}» a la Papelera de reciclaje?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            try:
                self.manager.close_session_for_path(str(target))
            except Exception:
                pass
            send2trash(str(target))
            if self.active_document and Path(self.active_document).resolve() == target:
                self._set_active_document(None)
                self._show_welcome()
            self.explorer.refresh()
            self.save_status.setText(f"{target.name} enviado a la papelera")
        except Exception as exc:
            QMessageBox.critical(self, "Eliminar", str(exc))

    def _save(self) -> None:
        if not self.active_document:
            return
        self.save_status.setText("Guardando…")
        self.browser.page().runJavaScript(
            "window.__archyterStudio && window.__archyterStudio.save();"
        )
        QTimer.singleShot(450, lambda: self.save_status.setText("Guardado"))

    def _run_cell(self) -> None:
        if not self.active_document:
            return
        self.browser.page().runJavaScript(
            "window.__archyterStudio && window.__archyterStudio.runCell();"
        )

    def _stop_kernel(self) -> None:
        if not self.active_kernel_id:
            QMessageBox.information(
                self,
                "Kernel",
                "No hay un kernel activo.",
            )
            return

        try:
            self.manager.shutdown_kernel(self.active_kernel_id)
            self.active_kernel_id = None
            self.active_kernel_name = ""
            self.inspector.set_variables([])
            self.inspector.update_kernel(
                "Python 3",
                "detenido",
                "Kernel detenido.",
            )
            self.save_status.setText("Kernel detenido")
        except Exception as exc:
            QMessageBox.warning(self, "Kernel", str(exc))

    def _show_kernel_details(self) -> None:
        if not self.active_kernel_id:
            return

        QMessageBox.information(
            self,
            "Kernel activo",
            (
                f"Kernel: {self.active_kernel_name}\n"
                f"ID: {self.active_kernel_id}\n"
                f"Jupyter: {self.manager.base_url}"
            ),
        )

    def _open_terminal_window(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Archyter Studio — Terminal")
        dialog.setWindowIcon(app_icon())
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        dialog.setStyleSheet(APP_STYLE)
        dialog.resize(900, 560)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(10, 10, 10, 10)

        terminal = TerminalCard(self.root_dir)
        layout.addWidget(terminal)
        dialog.finished.connect(lambda _code: terminal.shutdown())
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        QTimer.singleShot(0, lambda: apply_light_titlebar(self))

    def _restart_kernel(self) -> None:
        if not self.active_kernel_id:
            QMessageBox.information(self, "Kernel", "No hay un kernel activo.")
            return
        try:
            self.manager.restart_kernel(self.active_kernel_id)
            self.save_status.setText("Kernel reiniciado")
        except Exception as exc:
            QMessageBox.warning(self, "Kernel", str(exc))

    def _refresh_variables(self) -> None:
        if not self.active_kernel_id:
            self.inspector.set_variables([])
            return
        try:
            variables = self.manager.variable_snapshot(
                self.active_kernel_id,
                self.active_kernel_name,
            )
            self.inspector.set_variables(variables)
        except Exception as exc:
            self.inspector.set_variables([])
            self._append_log(f"Variables: {exc}")

    def _focus_terminal(self) -> None:
        self.inspector.terminal.input.setFocus()

    def _choose_project(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self,
            "Abrir proyecto",
            self.root_dir,
            QFileDialog.Option.ShowDirsOnly,
        )
        if folder:
            self._switch_project(folder)

    def _switch_project(self, path: str) -> None:
        new_root = str(Path(path).resolve())
        if new_root == self.root_dir:
            return

        self.save_status.setText("Cambiando proyecto…")
        QApplication.processEvents()

        self.manager.shutdown()
        self.root_dir = new_root
        self.settings.setValue("last_project", self.root_dir)
        self.active_document = None
        self.active_kernel_id = None
        self.active_kernel_name = ""
        self.started_at = time.time()

        self.explorer.set_root(self.root_dir)
        self.explorer.add_recent(self.root_dir)
        self.inspector.terminal.set_working_directory(self.root_dir)
        self.inspector.set_variables([])
        self._set_active_document(None)
        self.project_status.setText(self.root_dir)

        self.manager = JupyterManager(self.root_dir)
        self._wire_manager()
        self._start_jupyter()

    def _show_welcome(self) -> None:
        self._set_active_document(None)
        project_name = Path(self.root_dir).name or self.root_dir
        safe_path = self.root_dir.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        html = f"""
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            html,body{{height:100%;margin:0;background:#fff;font-family:'Segoe UI',Arial,sans-serif;color:#172033}}
            .wrap{{height:100%;display:flex;align-items:center;justify-content:center}}
            .card{{width:min(660px,78%);border:1px solid #dbe6f0;border-radius:18px;padding:42px 48px;
                   box-shadow:0 16px 50px rgba(48,91,130,.08);background:linear-gradient(145deg,#ffffff,#f8fbff)}}
            .mark{{font-size:48px;font-weight:800;color:#168ed2;line-height:1}}
            h1{{font-size:30px;margin:12px 0 8px}} p{{color:#64748b;line-height:1.6}}
            .project{{margin-top:22px;padding:14px 16px;border-radius:10px;background:#eef7ff;color:#17639d;
                      border:1px solid #d0e8fb;font-weight:600;word-break:break-all}}
            .hint{{display:flex;gap:12px;margin-top:24px;flex-wrap:wrap}}
            .pill{{padding:9px 13px;border:1px solid #d8e4ef;border-radius:9px;color:#475569;background:#fff}}
          </style>
        </head>
        <body><div class="wrap"><div class="card">
          <div class="mark">A</div>
          <h1>Archyter Studio</h1>
          <p>Tu espacio de Jupyter para Windows. Crea un notebook o abre uno desde el proyecto.</p>
          <div class="project">{project_name}<br><span style="font-weight:400;font-size:12px">{safe_path}</span></div>
          <div class="hint"><div class="pill">＋ Nuevo notebook</div><div class="pill">📁 Proyecto</div><div class="pill">⌨ PowerShell</div></div>
        </div></div></body></html>
        """
        self.browser.setHtml(html)
        self.save_status.setText("Listo")

    def _on_location_changed(self, directory: str) -> None:
        self.project_status.setText(directory)

    def _search_project(self) -> None:
        term, ok = QInputDialog.getText(
            self,
            "Buscar en proyecto",
            "Texto a buscar:",
        )
        term = term.strip()
        if not ok or not term:
            return

        allowed = {
            ".py", ".jl", ".md", ".txt", ".csv", ".json",
            ".yaml", ".yml", ".ipynb", ".toml",
        }
        matches: list[Path] = []
        root = Path(self.root_dir)

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            for path in root.rglob("*"):
                if len(matches) >= 80:
                    break
                if not path.is_file() or path.suffix.lower() not in allowed:
                    continue
                try:
                    if path.stat().st_size > 2_000_000:
                        continue
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                if term.casefold() in text.casefold():
                    matches.append(path)
        finally:
            QApplication.restoreOverrideCursor()

        if not matches:
            QMessageBox.information(
                self,
                "Buscar en proyecto",
                f"No encontré «{term}» en los archivos de este proyecto.",
            )
            return

        labels = [str(path.relative_to(root)) for path in matches]
        selected, accepted = QInputDialog.getItem(
            self,
            "Resultados de búsqueda",
            f"{len(matches)} archivo(s) con «{term}»:",
            labels,
            0,
            False,
        )
        if accepted and selected:
            self._open_file(str(root / selected))

    def _git_status(self) -> None:
        self._focus_terminal()
        self.inspector.terminal.send_command("git status --short --branch")

    def _show_settings(self) -> None:
        port = self.manager.port if self.manager.port is not None else "detenido"
        QMessageBox.information(
            self,
            "Archyter Studio",
            (
                f"Proyecto:\n{self.root_dir}\n\n"
                f"Python:\n{sys.executable}\n\n"
                f"Terminal: {self.inspector.terminal.shell_name}\n"
                f"Jupyter local: {port}\n"
                "Codificación: UTF-8"
            ),
        )

    def closeEvent(self, event) -> None:
        if hasattr(self, "state_timer"):
            self.state_timer.stop()
        if hasattr(self, "dirty_timer"):
            self.dirty_timer.stop()
        if hasattr(self, "inspector"):
            self.inspector.terminal.shutdown()
        self.manager.shutdown()
        super().closeEvent(event)
