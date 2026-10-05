from __future__ import annotations

import json
import uuid
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .icons import icon


class NotebookCell(QFrame):
    run_requested = Signal(str, str)
    activated = Signal(str)
    changed = Signal()

    def __init__(self, cell: dict, index: int):
        super().__init__()
        self.setObjectName("NativeCell")
        self.cell_id = str(cell.get("id") or uuid.uuid4().hex[:8])
        self.cell_type = str(cell.get("cell_type") or "code")
        self.execution_count = cell.get("execution_count")
        self.outputs = list(cell.get("outputs") or [])

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 7, 8, 7)
        layout.setSpacing(7)

        gutter = QVBoxLayout()
        gutter.setContentsMargins(0, 2, 0, 0)
        self.exec_label = QLabel(
            f"[{self.execution_count if self.execution_count is not None else ' '}]:"
            if self.cell_type == "code"
            else "M"
        )
        self.exec_label.setObjectName("CellPrompt")
        self.exec_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        self.exec_label.setFixedWidth(42)
        gutter.addWidget(self.exec_label)

        self.run_button = QPushButton()
        self.run_button.setObjectName("CellRunButton")
        self.run_button.setIcon(icon("run"))
        self.run_button.setFixedSize(28, 25)
        self.run_button.setToolTip("Ejecutar celda")
        self.run_button.setVisible(self.cell_type == "code")
        self.run_button.clicked.connect(self._run)
        gutter.addWidget(self.run_button)
        gutter.addStretch(1)
        layout.addLayout(gutter)

        body = QVBoxLayout()
        body.setSpacing(6)

        self.editor = QPlainTextEdit()
        self.editor.setObjectName("CellEditor")
        self.editor.setTabStopDistance(28)
        font = QFont("Cascadia Mono", 10)
        self.editor.setFont(font)
        self.editor.setPlaceholderText(
            "Escribe código Python…"
            if self.cell_type == "code"
            else "Escribe Markdown…"
        )
        source = cell.get("source") or []
        if isinstance(source, list):
            source = "".join(str(part) for part in source)
        self.editor.setPlainText(str(source))
        self.editor.textChanged.connect(self.changed.emit)
        self.editor.cursorPositionChanged.connect(
            lambda: self.activated.emit(self.cell_id)
        )
        self.editor.setMinimumHeight(74)
        self.editor.setMaximumHeight(260)
        body.addWidget(self.editor)

        self.output = QPlainTextEdit()
        self.output.setObjectName("CellOutput")
        self.output.setReadOnly(True)
        self.output.setVisible(False)
        self.output.setMaximumHeight(220)
        body.addWidget(self.output)

        layout.addLayout(body, 1)
        self._render_saved_outputs()

    def _render_saved_outputs(self) -> None:
        chunks: list[str] = []
        for output in self.outputs:
            output_type = output.get("output_type")
            if output_type == "stream":
                text = output.get("text") or ""
                if isinstance(text, list):
                    text = "".join(text)
                chunks.append(str(text))
            elif output_type in {"execute_result", "display_data"}:
                data = output.get("data") or {}
                plain = data.get("text/plain") or ""
                if isinstance(plain, list):
                    plain = "".join(plain)
                chunks.append(str(plain))
            elif output_type == "error":
                traceback = output.get("traceback") or []
                chunks.append("\n".join(str(item) for item in traceback))

        rendered = "".join(chunks).strip()
        if rendered:
            self.output.setPlainText(rendered)
            self.output.setVisible(True)

    def _run(self) -> None:
        self.activated.emit(self.cell_id)
        self.run_requested.emit(
            self.cell_id,
            self.editor.toPlainText(),
        )

    def set_active(self, active: bool) -> None:
        self.setProperty("active", active)
        self.style().unpolish(self)
        self.style().polish(self)

    def set_result(
        self,
        text: str,
        failed: bool,
        execution_count: int,
    ) -> None:
        self.execution_count = execution_count or self.execution_count
        self.exec_label.setText(
            f"[{self.execution_count if self.execution_count is not None else ' '}]:"
        )
        self.output.setProperty("error", failed)
        self.output.setPlainText(text)
        self.output.setVisible(bool(text))
        self.output.style().unpolish(self.output)
        self.output.style().polish(self.output)

    def to_json(self) -> dict:
        source = self.editor.toPlainText()
        if self.cell_type == "code":
            outputs: list[dict] = []
            if self.output.isVisible() and self.output.toPlainText():
                outputs.append(
                    {
                        "name": "stdout",
                        "output_type": "stream",
                        "text": self.output.toPlainText() + "\n",
                    }
                )
            return {
                "cell_type": "code",
                "execution_count": self.execution_count,
                "id": self.cell_id,
                "metadata": {},
                "outputs": outputs,
                "source": [source],
            }

        return {
            "cell_type": "markdown",
            "id": self.cell_id,
            "metadata": {},
            "source": [source],
        }


class NativeNotebookEditor(QFrame):
    dirty_changed = Signal(bool)
    execute_requested = Signal(str, str)
    active_cell_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self.setObjectName("NativeNotebook")
        self.path: Path | None = None
        self.metadata: dict = {}
        self.nbformat = 4
        self.nbformat_minor = 5
        self.cells: list[NotebookCell] = []
        self.active_cell_id: str | None = None
        self._dirty = False

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        toolbar = QFrame()
        toolbar.setObjectName("NativeNotebookToolbar")
        row = QHBoxLayout(toolbar)
        row.setContentsMargins(8, 4, 8, 4)
        row.setSpacing(6)

        self.add_code_button = QPushButton("＋ Celda")
        self.add_code_button.setObjectName("NotebookToolButton")
        self.add_code_button.clicked.connect(self.add_code_cell)
        row.addWidget(self.add_code_button)

        self.add_markdown_button = QPushButton("Markdown")
        self.add_markdown_button.setObjectName("NotebookToolButton")
        self.add_markdown_button.clicked.connect(self.add_markdown_cell)
        row.addWidget(self.add_markdown_button)
        row.addStretch(1)

        self.kernel_label = QLabel("Python 3")
        self.kernel_label.setObjectName("Muted")
        row.addWidget(self.kernel_label)
        root.addWidget(toolbar)

        self.scroll = QScrollArea()
        self.scroll.setObjectName("NotebookScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.container = QWidget()
        self.cells_layout = QVBoxLayout(self.container)
        self.cells_layout.setContentsMargins(14, 12, 14, 60)
        self.cells_layout.setSpacing(10)
        self.cells_layout.addStretch(1)
        self.scroll.setWidget(self.container)
        root.addWidget(self.scroll, 1)

    @property
    def dirty(self) -> bool:
        return self._dirty

    def _set_dirty(self, value: bool) -> None:
        if self._dirty == value:
            return
        self._dirty = value
        self.dirty_changed.emit(value)

    def clear(self) -> None:
        for cell in self.cells:
            cell.setParent(None)
            cell.deleteLater()
        self.cells.clear()
        self.active_cell_id = None
        self.path = None

    def load_file(self, path: str) -> None:
        target = Path(path).resolve()
        payload = json.loads(target.read_text(encoding="utf-8"))

        self.clear()
        self.path = target
        self.metadata = dict(payload.get("metadata") or {})
        self.nbformat = int(payload.get("nbformat") or 4)
        self.nbformat_minor = int(payload.get("nbformat_minor") or 5)

        cells = list(payload.get("cells") or [])
        if not cells:
            cells = [
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [],
                }
            ]

        for index, cell_data in enumerate(cells):
            self._append_cell(dict(cell_data), index)

        self._set_dirty(False)
        if self.cells:
            self.activate_cell(self.cells[0].cell_id)
            self.cells[0].editor.setFocus(Qt.FocusReason.OtherFocusReason)

    def _append_cell(self, cell_data: dict, index: int | None = None) -> NotebookCell:
        cell = NotebookCell(cell_data, len(self.cells))
        cell.run_requested.connect(self.execute_requested.emit)
        cell.activated.connect(self.activate_cell)
        cell.changed.connect(lambda: self._set_dirty(True))

        insert_at = len(self.cells) if index is None else index
        self.cells.insert(insert_at, cell)
        self.cells_layout.insertWidget(insert_at, cell)
        return cell

    def add_code_cell(self) -> None:
        cell = self._append_cell(
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [],
            }
        )
        self._set_dirty(True)
        self.activate_cell(cell.cell_id)
        cell.editor.setFocus(Qt.FocusReason.OtherFocusReason)

    def add_markdown_cell(self) -> None:
        cell = self._append_cell(
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [],
            }
        )
        self._set_dirty(True)
        self.activate_cell(cell.cell_id)
        cell.editor.setFocus(Qt.FocusReason.OtherFocusReason)

    def activate_cell(self, cell_id: str) -> None:
        self.active_cell_id = cell_id
        for cell in self.cells:
            cell.set_active(cell.cell_id == cell_id)
        self.active_cell_changed.emit(cell_id)

    def active_cell(self) -> NotebookCell | None:
        for cell in self.cells:
            if cell.cell_id == self.active_cell_id:
                return cell
        return self.cells[0] if self.cells else None

    def execute_active(self) -> None:
        cell = self.active_cell()
        if not cell or cell.cell_type != "code":
            return
        cell._run()

    def apply_execution_result(
        self,
        request_id: str,
        text: str,
        failed: bool,
        execution_count: int,
    ) -> None:
        for cell in self.cells:
            if cell.cell_id == request_id:
                cell.set_result(text, failed, execution_count)
                self._set_dirty(True)
                return

    def save(self) -> None:
        if self.path is None:
            return

        payload = {
            "cells": [cell.to_json() for cell in self.cells],
            "metadata": self.metadata,
            "nbformat": self.nbformat,
            "nbformat_minor": self.nbformat_minor,
        }
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
            encoding="utf-8",
        )
        self._set_dirty(False)
