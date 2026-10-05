from __future__ import annotations

import json
import os
from pathlib import Path

from PySide6.QtCore import QDir, QModelIndex, QSettings, QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFileSystemModel,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QStyle,
    QTreeView,
    QVBoxLayout,
)

from .animated import AnimatedToolButton
from .delegates import CleanProjectTree, CleanTreeDelegate
from .icons import icon


class StudioFileSystemModel(QFileSystemModel):
    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DecorationRole and index.column() == 0:
            path = Path(self.filePath(index))
            if self.isDir(index):
                return icon("folder", QStyle.StandardPixmap.SP_DirIcon)

            suffix = path.suffix.lower()
            if suffix == ".ipynb":
                return icon("notebook", QStyle.StandardPixmap.SP_FileIcon)
            if suffix == ".py":
                return icon("python", QStyle.StandardPixmap.SP_FileIcon)
            if suffix == ".csv":
                return icon("csv", QStyle.StandardPixmap.SP_FileIcon)
            if suffix in {".png", ".jpg", ".jpeg", ".webp", ".svg"}:
                return icon("image", QStyle.StandardPixmap.SP_FileIcon)
            if suffix in {".md", ".markdown"}:
                return icon("markdown", QStyle.StandardPixmap.SP_FileIcon)
            return icon("file", QStyle.StandardPixmap.SP_FileIcon)

        return super().data(index, role)


class ExplorerPanel(QFrame):
    file_open_requested = Signal(str)
    project_requested = Signal(str)
    new_requested = Signal(str)
    delete_requested = Signal(str)
    location_changed = Signal(str)

    def __init__(self, root_dir: str):
        super().__init__()
        self.setObjectName("Explorer")
        self.root_dir = os.path.abspath(root_dir)
        self._current_directory = self.root_dir
        self._active_path: str | None = None
        self.settings = QSettings("EduardoMedinaLabs", "ArchyterStudio")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(7)

        header = QHBoxLayout()
        header.setSpacing(5)

        title = QLabel("PROYECTO")
        title.setObjectName("SectionTitle")
        header.addWidget(title)
        header.addStretch(1)

        self.new_button = AnimatedToolButton(base_icon=18, hover_icon=20)
        self.new_button.setObjectName("IconButton")
        self.new_button.setIcon(icon("add"))
        self.new_button.setIconSize(QSize(18, 18))
        self.new_button.setToolTip("Crear en la carpeta seleccionada")
        self.new_button.setPopupMode(
            self.new_button.ToolButtonPopupMode.InstantPopup
        )

        menu = QMenu(self.new_button)
        notebook = menu.addAction(icon("notebook"), "Notebook")
        folder = menu.addAction(icon("folder"), "Carpeta")
        text_file = menu.addAction(icon("file"), "Archivo de texto")
        notebook.triggered.connect(lambda: self.new_requested.emit("notebook"))
        folder.triggered.connect(lambda: self.new_requested.emit("folder"))
        text_file.triggered.connect(lambda: self.new_requested.emit("file"))
        self.new_button.setMenu(menu)

        self.delete_button = AnimatedToolButton(base_icon=17, hover_icon=19)
        self.delete_button.setObjectName("DeleteButton")
        self.delete_button.setIcon(icon("trash"))
        self.delete_button.setToolTip(
            "Enviar archivo seleccionado a la Papelera de reciclaje"
        )
        self.delete_button.setEnabled(False)
        self.delete_button.clicked.connect(self._delete_selected)

        header.addWidget(self.new_button)
        header.addWidget(self.delete_button)
        layout.addLayout(header)

        self.path_label = QLabel(self._display_location(self.root_dir))
        self.path_label.setObjectName("ProjectPath")
        self.path_label.setToolTip(self.root_dir)
        # The approved Windows layout starts the tree directly below
        # the project header. Keep the breadcrumb for status/tooltips only.
        self.path_label.hide()

        self.model = StudioFileSystemModel(self)
        self.model.setReadOnly(True)
        self.model.setFilter(
            QDir.Filter.AllDirs
            | QDir.Filter.Files
            | QDir.Filter.NoDotAndDotDot
        )
        self.model.setRootPath(self.root_dir)

        self.tree = CleanProjectTree()
        self.tree.setObjectName("ProjectTree")
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(self.root_dir))
        self.tree.setHeaderHidden(True)
        self.tree.setAnimated(True)
        self.tree.setMouseTracking(True)
        self.tree.setIndentation(15)
        self.tree.setIconSize(QSize(18, 18))
        self.tree.setRootIsDecorated(True)
        self.tree.setItemsExpandable(True)
        self.tree.setItemDelegate(CleanTreeDelegate(self.tree))
        self.tree.setUniformRowHeights(True)
        self.tree.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)
        self.tree.setExpandsOnDoubleClick(True)
        self.tree.setAllColumnsShowFocus(False)
        self.tree.clicked.connect(self._clicked)
        self.tree.doubleClicked.connect(self._double_clicked)
        self.tree.selectionModel().selectionChanged.connect(
            lambda *_args: self._update_delete_state()
        )

        for column in range(1, 4):
            self.tree.hideColumn(column)

        layout.addWidget(self.tree, 1)

        recent_title = QLabel("PROYECTOS RECIENTES")
        recent_title.setObjectName("SectionTitle")
        layout.addWidget(recent_title)

        self.recents = QListWidget()
        self.recents.setObjectName("RecentProjects")
        self.recents.setIconSize(QSize(19, 19))
        self.recents.setMaximumHeight(160)
        self.recents.itemActivated.connect(self._open_recent)
        self.recents.itemClicked.connect(self._open_recent)
        layout.addWidget(self.recents)
        self.reload_recents()

    def _display_location(self, path: str) -> str:
        path_obj = Path(path)

        try:
            relative = path_obj.resolve().relative_to(
                Path(self.root_dir).resolve()
            )
            if str(relative) == ".":
                return Path(self.root_dir).name or self.root_dir
            return f"{Path(self.root_dir).name} / {relative.as_posix()}"
        except ValueError:
            return path_obj.name or str(path_obj)

    def current_directory(self) -> str:
        return self._current_directory

    def selected_path(self) -> str | None:
        indexes = self.tree.selectionModel().selectedRows(0)
        if not indexes:
            return None
        return self.model.filePath(indexes[0])

    def _clicked(self, index: QModelIndex) -> None:
        path = self.model.filePath(index)
        directory = path if os.path.isdir(path) else os.path.dirname(path)
        self._current_directory = directory
        self.path_label.setText(self._display_location(directory))
        self.path_label.setToolTip(directory)
        self.location_changed.emit(directory)
        self._update_delete_state()

    def _double_clicked(self, index: QModelIndex) -> None:
        path = self.model.filePath(index)
        if os.path.isfile(path):
            self.set_active_path(path)
            self.file_open_requested.emit(path)

    def _update_delete_state(self) -> None:
        path = self.selected_path()
        self.delete_button.setEnabled(bool(path and os.path.isfile(path)))

    def _delete_selected(self) -> None:
        path = self.selected_path()
        if path and os.path.isfile(path):
            self.delete_requested.emit(path)

    def set_active_path(self, path: str) -> None:
        resolved = os.path.abspath(path)
        self._active_path = resolved

        index = self.model.index(resolved)
        if index.isValid():
            self.tree.setCurrentIndex(index)
            self.tree.scrollTo(index, QTreeView.ScrollHint.PositionAtCenter)

            parent = index.parent()
            while parent.isValid():
                self.tree.expand(parent)
                parent = parent.parent()

        self._current_directory = os.path.dirname(resolved)
        self.path_label.setText(
            self._display_location(self._current_directory)
        )
        self.path_label.setToolTip(self._current_directory)
        self._update_delete_state()

    def refresh(self) -> None:
        root = self.root_dir
        self.model.setRootPath("")
        self.model.setRootPath(root)
        self.tree.setRootIndex(self.model.index(root))

        if self._active_path and os.path.exists(self._active_path):
            self.set_active_path(self._active_path)
        else:
            self._active_path = None
            self.delete_button.setEnabled(False)

    def set_root(self, root_dir: str) -> None:
        self.root_dir = os.path.abspath(root_dir)
        self._current_directory = self.root_dir
        self._active_path = None

        self.model.setRootPath(self.root_dir)
        self.tree.setRootIndex(self.model.index(self.root_dir))
        self.tree.collapseAll()

        self.path_label.setText(self._display_location(self.root_dir))
        self.path_label.setToolTip(self.root_dir)
        self.delete_button.setEnabled(False)
        self.reload_recents()

    def add_recent(self, path: str) -> None:
        resolved = str(Path(path).resolve())
        raw = self.settings.value("recent_projects", "[]")

        try:
            values = json.loads(str(raw))
        except json.JSONDecodeError:
            values = []

        values = [
            item
            for item in values
            if item != resolved and Path(item).is_dir()
        ]
        values.insert(0, resolved)
        self.settings.setValue(
            "recent_projects",
            json.dumps(values[:6]),
        )
        self.reload_recents()

    def reload_recents(self) -> None:
        self.recents.clear()
        raw = self.settings.value("recent_projects", "[]")

        try:
            values = json.loads(str(raw))
        except json.JSONDecodeError:
            values = []

        for value in values:
            path = Path(value)
            if not path.is_dir():
                continue

            item = QListWidgetItem(
                icon("folder"),
                f"{path.name or path}\n{path}",
            )
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            item.setToolTip(str(path))
            item.setSizeHint(QSize(0, 48))
            self.recents.addItem(item)

    def _open_recent(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.ItemDataRole.UserRole)
        if (
            path
            and Path(path).is_dir()
            and os.path.abspath(path) != self.root_dir
        ):
            self.project_requested.emit(str(path))
