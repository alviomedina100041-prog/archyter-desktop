from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QDir, QModelIndex, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFileSystemModel,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QStyle,
    QToolButton,
    QTreeView,
    QVBoxLayout,
)

from ..icons import themed_icon


class ArchyterFileSystemModel(QFileSystemModel):
    def __init__(self, parent=None):
        super().__init__(parent)

        style = QApplication.instance().style()
        file_fallback = style.standardIcon(QStyle.StandardPixmap.SP_FileIcon)
        folder_fallback = style.standardIcon(QStyle.StandardPixmap.SP_DirIcon)

        self.folder_icon = themed_icon(
            "folder",
            QStyle.StandardPixmap.SP_DirIcon,
        )
        self.file_icon = file_fallback
        self.notebook_icon = QIcon.fromTheme("application-x-ipynb", file_fallback)
        self.python_icon = QIcon.fromTheme("text-x-python", file_fallback)
        self.julia_icon = QIcon.fromTheme("text-x-julia", file_fallback)
        self.text_icon = QIcon.fromTheme("text-x-generic", file_fallback)

        if self.folder_icon.isNull():
            self.folder_icon = folder_fallback

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if role == Qt.DecorationRole and index.column() == 0:
            path = Path(self.filePath(index))

            if self.isDir(index):
                return self.folder_icon

            suffix = path.suffix.lower()
            if suffix == ".ipynb":
                return self.notebook_icon
            if suffix == ".py":
                return self.python_icon
            if suffix == ".jl":
                return self.julia_icon
            if suffix in {".md", ".txt", ".csv", ".json", ".yaml", ".yml"}:
                return self.text_icon

            return self.file_icon

        return super().data(index, role)


class FileExplorerPanel(QFrame):
    file_open_requested = Signal(str)
    location_changed = Signal(str)
    new_requested = Signal(str)
    delete_requested = Signal(str)

    def __init__(self, root_dir: str):
        super().__init__()
        self.setObjectName("Sidebar")

        self.root_dir = os.path.abspath(root_dir)
        self._current_directory = self.root_dir
        self._active_path: str | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(7)

        header = QHBoxLayout()
        header.setSpacing(4)

        title = QLabel("Archivos")
        title.setObjectName("SectionTitle")

        self.new_btn = QToolButton()
        self.new_btn.setObjectName("ExplorerToolButton")
        self.new_btn.setIcon(
            themed_icon(
                "document-new",
                QStyle.StandardPixmap.SP_FileDialogNewFolder,
            )
        )
        self.new_btn.setToolTip("Crear dentro de la carpeta seleccionada")
        self.new_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        new_menu = QMenu(self.new_btn)
        notebook_action = new_menu.addAction(
            themed_icon("application-x-ipynb"),
            "Notebook",
        )
        folder_action = new_menu.addAction(
            themed_icon("folder-new", QStyle.StandardPixmap.SP_FileDialogNewFolder),
            "Carpeta",
        )
        file_action = new_menu.addAction(
            themed_icon("text-x-generic"),
            "Archivo de texto",
        )

        notebook_action.triggered.connect(
            lambda: self.new_requested.emit("notebook")
        )
        folder_action.triggered.connect(
            lambda: self.new_requested.emit("folder")
        )
        file_action.triggered.connect(
            lambda: self.new_requested.emit("file")
        )
        self.new_btn.setMenu(new_menu)

        self.refresh_btn = QToolButton()
        self.refresh_btn.setObjectName("ExplorerToolButton")
        self.refresh_btn.setIcon(
            themed_icon(
                "view-refresh",
                QStyle.StandardPixmap.SP_BrowserReload,
            )
        )
        self.refresh_btn.setToolTip("Actualizar explorador")
        self.refresh_btn.clicked.connect(self.refresh)

        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self.new_btn)
        header.addWidget(self.refresh_btn)
        layout.addLayout(header)

        self.location_label = QLabel(self._display_location(self._current_directory))
        self.location_label.setObjectName("ProjectChip")
        self.location_label.setToolTip(self._current_directory)
        layout.addWidget(self.location_label)

        self.model = ArchyterFileSystemModel(self)
        self.model.setReadOnly(True)
        self.model.setFilter(
            QDir.Filter.AllDirs
            | QDir.Filter.Files
            | QDir.Filter.NoDotAndDotDot
        )
        self.model.setRootPath(self.root_dir)

        self.tree = QTreeView()
        self.tree.setObjectName("FileTree")
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(self.root_dir))
        self.tree.setHeaderHidden(True)
        self.tree.setAnimated(True)
        self.tree.setIndentation(15)
        self.tree.setIconSize(self.tree.iconSize().expandedTo(self.tree.iconSize()))
        self.tree.setUniformRowHeights(True)
        self.tree.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)
        self.tree.clicked.connect(self._on_clicked)
        self.tree.doubleClicked.connect(self._on_double_click)

        # A real delete control replaces the ambiguous empty blue block that
        # appears in the indentation area of the selected file row.
        self.delete_btn = QToolButton(self.tree.viewport())
        self.delete_btn.setObjectName("ExplorerDeleteButton")
        self.delete_btn.setIcon(
            themed_icon(
                "user-trash",
                QStyle.StandardPixmap.SP_TrashIcon,
            )
        )
        self.delete_btn.setToolTip("Enviar archivo seleccionado a la papelera")
        self.delete_btn.setFixedSize(24, 22)
        self.delete_btn.hide()
        self.delete_btn.clicked.connect(self._request_delete_selected)

        self.tree.selectionModel().selectionChanged.connect(
            lambda *_args: self._position_delete_button()
        )
        self.tree.verticalScrollBar().valueChanged.connect(
            lambda _value: self._position_delete_button()
        )
        self.tree.expanded.connect(
            lambda _index: self._position_delete_button()
        )
        self.tree.collapsed.connect(
            lambda _index: self._position_delete_button()
        )

        for i in range(1, 4):
            self.tree.hideColumn(i)

        layout.addWidget(self.tree, 1)

    def _selected_file_path(self) -> str | None:
        path = self.selected_path()
        if not path or not os.path.isfile(path):
            return None
        return os.path.abspath(path)

    def _request_delete_selected(self) -> None:
        path = self._selected_file_path()
        if not path:
            self.delete_btn.hide()
            return
        self.delete_requested.emit(path)

    def _position_delete_button(self) -> None:
        path = self._selected_file_path()
        if not path:
            self.delete_btn.hide()
            return

        index = self.model.index(path)
        if not index.isValid():
            self.delete_btn.hide()
            return

        rect = self.tree.visualRect(index)
        if not rect.isValid() or not self.tree.viewport().rect().intersects(rect):
            self.delete_btn.hide()
            return

        x = 3
        y = rect.top() + max(
            0,
            (rect.height() - self.delete_btn.height()) // 2,
        )
        self.delete_btn.move(x, y)
        self.delete_btn.show()
        self.delete_btn.raise_()

    def _display_location(self, path: str) -> str:
        location = Path(path)

        try:
            relative = location.relative_to(self.root_dir)
        except ValueError:
            return location.name or str(location)

        if str(relative) == ".":
            return Path(self.root_dir).name or self.root_dir

        return f"{Path(self.root_dir).name} / {relative.as_posix()}"

    def current_directory(self) -> str:
        return self._current_directory

    def selected_path(self) -> str | None:
        indexes = self.tree.selectionModel().selectedRows(0)
        if not indexes:
            return None
        return self.model.filePath(indexes[0])

    def _set_location(self, path: str) -> None:
        directory = os.path.abspath(path)
        if not os.path.isdir(directory):
            directory = os.path.dirname(directory)

        if not directory:
            directory = self.root_dir

        self._current_directory = directory
        self.location_label.setText(self._display_location(directory))
        self.location_label.setToolTip(directory)
        self.location_changed.emit(directory)

    def _on_clicked(self, index: QModelIndex) -> None:
        path = self.model.filePath(index)
        self._set_location(path)
        self._position_delete_button()

    def _on_double_click(self, index: QModelIndex) -> None:
        path = self.model.filePath(index)

        if os.path.isdir(path):
            self._set_location(path)
            return

        if os.path.isfile(path):
            self.set_active_path(path)
            self.file_open_requested.emit(path)

    def set_active_path(self, path: str) -> None:
        resolved = os.path.abspath(path)
        self._active_path = resolved

        index = self.model.index(resolved)
        if index.isValid():
            self.tree.setCurrentIndex(index)
            self.tree.scrollTo(
                index,
                QTreeView.ScrollHint.PositionAtCenter,
            )
            parent = index.parent()
            while parent.isValid():
                self.tree.expand(parent)
                parent = parent.parent()

        self._set_location(os.path.dirname(resolved))
        self._position_delete_button()

    def refresh(self) -> None:
        current_root = self.root_dir
        self.model.setRootPath("")
        self.model.setRootPath(current_root)
        self.tree.setRootIndex(self.model.index(current_root))

        if self._active_path and os.path.exists(self._active_path):
            self.set_active_path(self._active_path)
        else:
            self._active_path = None
            self.delete_btn.hide()

    def set_root(self, root_dir: str) -> None:
        self.root_dir = os.path.abspath(root_dir)
        self._current_directory = self.root_dir
        self._active_path = None

        self.location_label.setText(self._display_location(self.root_dir))
        self.location_label.setToolTip(self.root_dir)

        self.model.setRootPath(self.root_dir)
        self.tree.setRootIndex(self.model.index(self.root_dir))
        self.tree.collapseAll()
        self.delete_btn.hide()
