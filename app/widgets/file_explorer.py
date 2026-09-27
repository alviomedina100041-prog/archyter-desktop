from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFileSystemModel, QFrame, QHBoxLayout, QLabel, QPushButton, QTreeView, QVBoxLayout


class FileExplorerPanel(QFrame):
    file_open_requested = Signal(str)

    def __init__(self, root_dir: str):
        super().__init__()
        self.setObjectName("Sidebar")
        self.root_dir = root_dir

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("Explorador de archivos")
        title.setObjectName("SectionTitle")
        add_btn = QPushButton("+")
        add_btn.setFixedWidth(34)
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(add_btn)
        layout.addLayout(header)

        project_label = QLabel(f"Proyecto: {Path(root_dir).name}")
        project_label.setObjectName("MutedLabel")
        layout.addWidget(project_label)

        self.model = QFileSystemModel(self)
        self.model.setRootPath(root_dir)
        self.model.setReadOnly(True)

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(root_dir))
        self.tree.setHeaderHidden(True)
        self.tree.setAnimated(True)
        self.tree.setIndentation(18)
        self.tree.doubleClicked.connect(self._on_double_click)

        for i in range(1, 4):
            self.tree.hideColumn(i)

        layout.addWidget(self.tree, 1)

    def _on_double_click(self, index) -> None:
        path = self.model.filePath(index)
        if os.path.isfile(path):
            self.file_open_requested.emit(path)
