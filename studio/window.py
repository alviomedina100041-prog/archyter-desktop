from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from send2trash import send2trash
from PySide6.QtCore import QSettings, QTimer, Qt
from PySide6.QtGui import QKeySequence, QShortcut
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
    QStackedWidget,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .animated import AnimatedPushButton, AnimatedToolButton, add_soft_shadow
from .explorer import ExplorerPanel
from .icons import app_icon, icon
from .inspector import InspectorPanel
from .native_kernel import NativeKernelController
from .native_notebook import NativeNotebookEditor
from .terminal import TerminalCard
from .theme import APP_STYLE
from .windows_chrome import apply_light_titlebar


class StudioWindow(QMainWindow):
    def __init__(self, root_dir: str):
        super().__init__()
        self.root_dir = str(Path(root_dir).resolve())
        self.settings = QSettings("EduardoMedinaLabs", "ArchyterStudio")
        self.settings.setValue("last_project", self.root_dir)

        self.active_document: str | None = None
        self.kernel = NativeKernelController(self.root_dir)
        self.kernel_state = "starting"
        self.kernel_name = "python3"
        self._closing = False
        self._responsive_mode: str | None = None

        self.setWindowTitle("Archyter Studio")
        self.setWindowIcon(app_icon())
        self.resize(1480, 900)
        self.setMinimumSize(1120, 700)

        self._build_ui()
        self.setStyleSheet(APP_STYLE)
        self._connect_kernel()
        self._install_shortcuts()

        self.kernel.start()

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
        self.explorer.setMinimumWidth(205)
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
        self.inspector.setMinimumWidth(255)
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
        self.new_button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self.new_button.setPopupMode(
            QToolButton.ToolButtonPopupMode.InstantPopup
        )
        menu = QMenu(self.new_button)
        notebook = menu.addAction(icon("notebook"), "Notebook")
        folder = menu.addAction(icon("folder"), "Carpeta")
        text_file = menu.addAction(icon("file"), "Archivo de texto")
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
        self.run_button.setIcon(
            icon("play", QStyle.StandardPixmap.SP_MediaPlay)
        )
        self.run_button.setEnabled(False)
        self.run_button.clicked.connect(self._run_cell)
        layout.addWidget(self.run_button)

        self.kernel_button = AnimatedPushButton("Kernel")
        self.kernel_button.setIcon(icon("kernel"))
        self.kernel_button.setToolTip("Reiniciar kernel")
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
        search.setToolTip("Buscar en proyecto")
        search.clicked.connect(self._search_project)
        layout.addWidget(search)

        settings = AnimatedToolButton(base_icon=18, hover_icon=20)
        settings.setObjectName("IconButton")
        settings.setIcon(icon("settings"))
        settings.setToolTip("Configuración")
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
        layout.addWidget(document)

        self.editor_stack = QStackedWidget()

        self.welcome = QLabel(
            "<div style='text-align:center'>"
            "<div style='font-size:48px;color:#149fe2;font-weight:700'>A</div>"
            "<div style='font-size:24px;font-weight:700'>Archyter Studio</div>"
            "<div style='color:#718096;margin-top:8px'>"
            "Notebook IDE nativo para Windows"
            "</div></div>"
        )
        self.welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.welcome.setObjectName("StudioWelcome")

        self.notebook_editor = NativeNotebookEditor()
        self.notebook_editor.dirty_changed.connect(self._dirty_changed)
        self.notebook_editor.execute_requested.connect(self._execute_cell)

        self.editor_stack.addWidget(self.welcome)
        self.editor_stack.addWidget(self.notebook_editor)
        layout.addWidget(self.editor_stack, 1)

        self._show_welcome()
        return frame

    def _build_statusbar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("StatusBar")
        bar.setFixedHeight(31)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 3, 12, 3)
        layout.setSpacing(12)

        self.kernel_status = QLabel("python3 | iniciando")
        self.kernel_status.setObjectName("Muted")

        self.save_status = QLabel("Listo")
        self.save_status.setObjectName("StatusGood")

        self.project_status = QLabel(self.root_dir)
        self.project_status.setObjectName("Muted")
        self.project_status.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignVCenter
        )

        layout.addWidget(self.kernel_status)
        layout.addWidget(self.save_status)
        layout.addStretch(1)
        layout.addWidget(QLabel("UTF-8"))
        layout.addWidget(QLabel("Jupyter Kernel"))
        layout.addWidget(self.project_status)
        return bar

    def _connect_kernel(self) -> None:
        self.kernel.state_changed.connect(self._kernel_state_changed)
        self.kernel.execution_finished.connect(
            self._execution_finished
        )
        self.kernel.variables_ready.connect(
            self.inspector.set_variables
        )
        self.kernel.error.connect(self._kernel_error)

    def _install_shortcuts(self) -> None:
        QShortcut(
            QKeySequence.StandardKey.Save,
            self,
            activated=self._save,
        )
        QShortcut(
            QKeySequence("Shift+Return"),
            self,
            activated=self._run_cell,
        )
        QShortcut(
            QKeySequence("Ctrl+Return"),
            self,
            activated=self._run_cell,
        )

    def _kernel_state_changed(
        self,
        state: str,
        kernel_name: str,
    ) -> None:
        self.kernel_state = state
        self.kernel_name = kernel_name

        detail = {
            "starting": "Iniciando kernel nativo…",
            "busy": "Ejecutando celda…",
            "idle": "Kernel local listo",
            "dead": "Kernel detenido",
        }.get(state, state)

        self.kernel_status.setText(
            f"{kernel_name} | {state}"
        )
        self.inspector.update_kernel(
            kernel_name,
            state,
            detail,
        )

    def _kernel_error(self, message: str) -> None:
        self.save_status.setText("Error de kernel")
        QMessageBox.warning(
            self,
            "Kernel",
            message,
        )

    def _execute_cell(
        self,
        cell_id: str,
        code: str,
    ) -> None:
        if not code.strip():
            return

        self.save_status.setText("Ejecutando…")
        self.kernel.execute(
            code,
            request_id=cell_id,
        )

    def _execution_finished(
        self,
        request_id: str,
        output: str,
        failed: bool,
        execution_count: int,
    ) -> None:
        self.notebook_editor.apply_execution_result(
            request_id,
            output,
            failed,
            execution_count,
        )
        self.save_status.setText(
            "Error en celda" if failed else "Ejecutado"
        )
        self.kernel.refresh_variables()

    def _refresh_variables(self) -> None:
        self.kernel.refresh_variables()

    def _restart_kernel(self) -> None:
        self.inspector.set_variables([])
        self.kernel.restart()
        self.save_status.setText("Reiniciando kernel…")

    def _stop_kernel(self) -> None:
        self.kernel.shutdown()
        self.inspector.set_variables([])
        self._kernel_state_changed(
            "dead",
            self.kernel_name,
        )
        self.save_status.setText("Kernel detenido")

    def _show_kernel_details(self) -> None:
        QMessageBox.information(
            self,
            "Kernel",
            (
                f"Kernel: {self.kernel_name}\n"
                f"Estado: {self.kernel_state}\n"
                f"Python: {sys.executable}\n"
                f"Proyecto: {self.root_dir}"
            ),
        )

    def _open_file(self, path: str) -> None:
        target = Path(path).resolve()

        if target.suffix.lower() != ".ipynb":
            QMessageBox.information(
                self,
                "Abrir archivo",
                "Por ahora el editor central nativo abre notebooks .ipynb.",
            )
            return

        try:
            self.notebook_editor.load_file(str(target))
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Abrir notebook",
                str(exc),
            )
            return

        self.active_document = str(target)
        self.document_title.setText(target.name)
        self.document_tab.show()
        self.explorer.set_active_path(str(target))
        self.editor_stack.setCurrentWidget(self.notebook_editor)
        self.save_button.setEnabled(True)
        self.run_button.setEnabled(True)
        self.save_status.setText("Listo")

    def _show_welcome(self) -> None:
        self.active_document = None
        self.document_title.setText("Inicio")
        self.document_tab.hide()
        if hasattr(self, "editor_stack"):
            self.editor_stack.setCurrentWidget(self.welcome)
        if hasattr(self, "save_button"):
            self.save_button.setEnabled(False)
        if hasattr(self, "run_button"):
            self.run_button.setEnabled(False)

    def _dirty_changed(self, dirty: bool) -> None:
        self.save_status.setText(
            "Cambios sin guardar" if dirty else "Guardado"
        )

    def _save(self) -> None:
        if not self.active_document:
            return
        try:
            self.notebook_editor.save()
            self.save_status.setText("Guardado")
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Guardar notebook",
                str(exc),
            )

    def _run_cell(self) -> None:
        if not self.active_document:
            return
        self.notebook_editor.execute_active()

    def _handle_new(self, kind: str) -> None:
        directory = Path(self.explorer.current_directory())
        if not directory.is_dir():
            directory = Path(self.root_dir)

        if kind == "notebook":
            self._new_notebook(directory)
        elif kind == "folder":
            self._new_folder(directory)
        else:
            self._new_text_file(directory)

    def _new_notebook(self, directory: Path) -> None:
        base = "Untitled"
        target = directory / f"{base}.ipynb"
        counter = 1

        while target.exists():
            target = directory / f"{base}{counter}.ipynb"
            counter += 1

        payload = {
            "cells": [],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3 (ipykernel)",
                    "language": "python",
                    "name": "python3",
                },
                "language_info": {
                    "name": "python",
                },
            },
            "nbformat": 4,
            "nbformat_minor": 5,
        }

        try:
            target.write_text(
                json.dumps(
                    payload,
                    ensure_ascii=False,
                    indent=1,
                )
                + "\n",
                encoding="utf-8",
            )
            self.explorer.refresh()
            self._open_file(str(target))
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Nuevo notebook",
                str(exc),
            )

    def _new_folder(self, directory: Path) -> None:
        name, ok = QInputDialog.getText(
            self,
            "Nueva carpeta",
            "Nombre:",
        )
        name = name.strip()
        if not ok or not name:
            return

        if any(token in name for token in ("/", "\\")) or name in {".", ".."}:
            QMessageBox.warning(
                self,
                "Nueva carpeta",
                "Usa un nombre simple, sin rutas.",
            )
            return

        try:
            (directory / name).mkdir()
            self.explorer.refresh()
        except FileExistsError:
            QMessageBox.information(
                self,
                "Nueva carpeta",
                "Ya existe una carpeta con ese nombre.",
            )
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Nueva carpeta",
                str(exc),
            )

    def _new_text_file(self, directory: Path) -> None:
        name, ok = QInputDialog.getText(
            self,
            "Nuevo archivo",
            "Nombre:",
            text="notas.txt",
        )
        name = name.strip()
        if not ok or not name:
            return

        if any(token in name for token in ("/", "\\")) or name in {".", ".."}:
            QMessageBox.warning(
                self,
                "Nuevo archivo",
                "Usa un nombre simple, sin rutas.",
            )
            return

        target = directory / name
        if target.exists():
            QMessageBox.information(
                self,
                "Nuevo archivo",
                "Ya existe un archivo con ese nombre.",
            )
            return

        try:
            target.write_text("", encoding="utf-8")
            self.explorer.refresh()
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Nuevo archivo",
                str(exc),
            )

    def _delete_file(self, path: str) -> None:
        target = Path(path).resolve()

        try:
            target.relative_to(Path(self.root_dir).resolve())
        except ValueError:
            QMessageBox.warning(
                self,
                "Eliminar",
                "El archivo está fuera del proyecto.",
            )
            return

        if not target.is_file():
            self.explorer.refresh()
            return

        answer = QMessageBox.question(
            self,
            "Enviar a la papelera",
            f"¿Enviar «{target.name}» a la Papelera de reciclaje?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            send2trash(str(target))

            if (
                self.active_document
                and Path(self.active_document).resolve() == target
            ):
                self._show_welcome()

            self.explorer.refresh()
            self.save_status.setText(
                f"{target.name} enviado a la papelera"
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Eliminar",
                str(exc),
            )

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

        self.kernel.shutdown()

        self.root_dir = new_root
        self.settings.setValue("last_project", self.root_dir)
        self.explorer.set_root(self.root_dir)
        self.explorer.add_recent(self.root_dir)
        self.inspector.terminal.set_working_directory(self.root_dir)
        self.inspector.set_variables([])
        self.project_status.setText(self.root_dir)
        self._show_welcome()

        self.kernel = NativeKernelController(self.root_dir)
        self._connect_kernel()
        self.kernel.start()

    def _on_location_changed(self, directory: str) -> None:
        self.project_status.setText(directory)

    def _focus_terminal(self) -> None:
        self.inspector.terminal.input.setFocus()

    def _open_terminal_window(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Archyter Studio — Terminal")
        dialog.setWindowIcon(app_icon())
        dialog.setAttribute(
            Qt.WidgetAttribute.WA_DeleteOnClose,
            True,
        )
        dialog.setStyleSheet(APP_STYLE)
        dialog.resize(900, 560)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(10, 10, 10, 10)

        terminal = TerminalCard(self.root_dir)
        layout.addWidget(terminal)
        dialog.finished.connect(
            lambda _code: terminal.shutdown()
        )
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

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
            ".py",
            ".jl",
            ".md",
            ".txt",
            ".csv",
            ".json",
            ".yaml",
            ".yml",
            ".ipynb",
            ".toml",
        }
        matches: list[Path] = []
        root = Path(self.root_dir)

        QApplication.setOverrideCursor(
            Qt.CursorShape.WaitCursor
        )
        try:
            for path in root.rglob("*"):
                if len(matches) >= 80:
                    break
                if (
                    not path.is_file()
                    or path.suffix.lower() not in allowed
                ):
                    continue
                try:
                    if path.stat().st_size > 2_000_000:
                        continue
                    text = path.read_text(
                        encoding="utf-8",
                        errors="ignore",
                    )
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
                f"No encontré «{term}».",
            )
            return

        labels = [
            str(path.relative_to(root))
            for path in matches
        ]
        selected, accepted = QInputDialog.getItem(
            self,
            "Resultados",
            f"{len(matches)} archivo(s):",
            labels,
            0,
            False,
        )

        if accepted and selected:
            self._open_file(str(root / selected))

    def _git_status(self) -> None:
        self._focus_terminal()
        self.inspector.terminal.send_command(
            "git status --short --branch"
        )

    def _show_settings(self) -> None:
        QMessageBox.information(
            self,
            "Archyter Studio",
            (
                f"Proyecto:\n{self.root_dir}\n\n"
                f"Python:\n{sys.executable}\n\n"
                f"Kernel: {self.kernel_name}\n"
                f"Estado: {self.kernel_state}\n"
                f"Terminal: {self.inspector.terminal.shell_name}\n"
                "Render: Qt nativo (sin Chromium)\n"
                "Codificación: UTF-8"
            ),
        )

    def _apply_responsive_layout(self) -> None:
        if not hasattr(self, "splitter"):
            return

        width = self.width()

        if width < 1260:
            mode = "compact"
        elif width < 1500:
            mode = "medium"
        else:
            mode = "wide"

        if mode == self._responsive_mode:
            return

        self._responsive_mode = mode
        total = max(720, self.splitter.width())

        if mode == "compact":
            left = 210
            right = 265
        elif mode == "medium":
            left = 230
            right = 285
        else:
            left = 255
            right = 320

        center = max(
            420,
            total - left - right - 8,
        )
        self.splitter.setSizes(
            [left, center, right]
        )

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._apply_responsive_layout()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._apply_responsive_layout()
        QTimer.singleShot(
            0,
            lambda: apply_light_titlebar(self),
        )

    def closeEvent(self, event) -> None:
        self._closing = True
        self.inspector.terminal.shutdown()
        self.kernel.shutdown()
        super().closeEvent(event)
