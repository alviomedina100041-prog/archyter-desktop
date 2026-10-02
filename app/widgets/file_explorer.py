from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileSystemModel,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTreeView,
    QVBoxLayout,
)


class FileExplorerPanel(QFrame):
    file_open_requested = Signal(str)

    def __init__(self, root_dir: str):
        super().__init__()
        self.setObjectName("Sidebar")
        self.root_dir = os.path.abspath(root_dir)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(7)

        header = QHBoxLayout()
        header.setSpacing(4)

        title = QLabel("Archivos")
        title.setObjectName("SectionTitle")

        self.refresh_btn = QPushButton("↻")
        self.refresh_btn.setObjectName("IconButton")
        self.refresh_btn.setFixedWidth(28)
        self.refresh_btn.setToolTip("Actualizar explorador")
        self.refresh_btn.clicked.connect(self.refresh)

        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self.refresh_btn)
        layout.addLayout(header)

        self.project_label = QLabel(Path(self.root_dir).name or self.root_dir)
        self.project_label.setObjectName("ProjectChip")
        self.project_label.setToolTip(self.root_dir)
        layout.addWidget(self.project_label)

        self.model = QFileSystemModel(self)
        self.model.setReadOnly(True)
        self.model.setRootPath(self.root_dir)

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(self.root_dir))
        self.tree.setHeaderHidden(True)
        self.tree.setAnimated(True)
        self.tree.setIndentation(15)
        self.tree.setUniformRowHeights(True)
        self.tree.doubleClicked.connect(self._on_double_click)

        for i in range(1, 4):
            self.tree.hideColumn(i)

        layout.addWidget(self.tree, 1)

    def refresh(self) -> None:
        current_root = self.root_dir
        self.model.setRootPath("")
        self.model.setRootPath(current_root)
        self.tree.setRootIndex(self.model.index(current_root))

    def set_root(self, root_dir: str) -> None:
        self.root_dir = os.path.abspath(root_dir)
        self.project_label.setText(Path(self.root_dir).name or self.root_dir)
        self.project_label.setToolTip(self.root_dir)
        self.model.setRootPath(self.root_dir)
        self.tree.setRootIndex(self.model.index(self.root_dir))
        self.tree.collapseAll()

    def _on_double_click(self, index) -> None:
        path = self.model.filePath(index)
        if os.path.isfile(path):
            self.file_open_requested.emit(path)
