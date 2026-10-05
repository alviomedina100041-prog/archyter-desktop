from __future__ import annotations

import gc
import json
import uuid
from pathlib import Path

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QFont, QKeyEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QMenu,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .icons import icon


MAX_CELL_OUTPUT_CHARS = 120_000


def _bounded_output(text: str) -> str:
    if len(text) <= MAX_CELL_OUTPUT_CHARS:
        return text
    return (
        text[:MAX_CELL_OUTPUT_CHARS]
        + "\n[Salida truncada para proteger la memoria]"
    )


class AutoHeightPlainTextEdit(QPlainTextEdit):
    """Text editor that grows with its contents and stops before taking over the page."""

    def __init__(
        self,
        *,
        minimum_lines: int,
        maximum_lines: int,
        read_only: bool = False,
    ):
        super().__init__()
        self.minimum_lines = minimum_lines
        self.maximum_lines = maximum_lines
        self.setReadOnly(read_only)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.document().contentsChanged.connect(self.update_height)
        QTimer.singleShot(0, self.update_height)

    def update_height(self) -> None:
        metrics = self.fontMetrics()
        line_height = max(16, metrics.lineSpacing())
        blocks = max(
            self.minimum_lines,
            self.document().blockCount(),
        )
        visible_lines = min(blocks, self.maximum_lines)
        target = (
            visible_lines * line_height
            + 22
        )
        self.setFixedHeight(target)

        needs_scroll = blocks > self.maximum_lines
        self.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
            if needs_scroll
            else Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )


class NotebookCell(QFrame):
    run_requested = Signal(str, str)
    activated = Signal(str)
    changed = Signal()
    insert_below_requested = Signal(str, str)
    delete_requested = Signal(str)

    def __init__(self, cell: dict, index: int):
        super().__init__()
        self.setObjectName("NativeCell")
        self.cell_id = str(
            cell.get("id")
            or uuid.uuid4().hex[:8]
        )
        self.cell_type = str(
            cell.get("cell_type")
            or "code"
        )
        self.execution_count = cell.get(
            "execution_count"
        )
        self.outputs = list(
            cell.get("outputs")
            or []
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 6, 8, 8)
        root.setSpacing(5)

        header = QHBoxLayout()
        header.setSpacing(4)

        self.exec_label = QLabel(
            f"[{self.execution_count if self.execution_count is not None else ' '}]:"
            if self.cell_type == "code"
            else "Markdown"
        )
        self.exec_label.setObjectName("CellPrompt")
        header.addWidget(self.exec_label)

        self.type_label = QLabel(
            "Python"
            if self.cell_type == "code"
            else "Markdown"
        )
        self.type_label.setObjectName("CellType")
        header.addWidget(self.type_label)

        header.addStretch(1)

        self.run_button = QToolButton()
        self.run_button.setObjectName("CellActionButton")
        self.run_button.setIcon(icon("run"))
        self.run_button.setToolTip("Ejecutar celda")
        self.run_button.setVisible(
            self.cell_type == "code"
        )
        self.run_button.clicked.connect(self._run)
        header.addWidget(self.run_button)

        self.add_button = QToolButton()
        self.add_button.setObjectName("CellActionButton")
        self.add_button.setIcon(icon("add"))
        self.add_button.setToolTip(
            "Agregar celda de código debajo"
        )
        self.add_button.setPopupMode(
            QToolButton.ToolButtonPopupMode.InstantPopup
        )
        add_menu = QMenu(self.add_button)
        add_code = add_menu.addAction(
            icon("run"),
            "Código debajo",
        )
        add_markdown = add_menu.addAction(
            "Markdown debajo",
        )
        add_code.triggered.connect(
            lambda: self.insert_below_requested.emit(
                self.cell_id,
                "code",
            )
        )
        add_markdown.triggered.connect(
            lambda: self.insert_below_requested.emit(
                self.cell_id,
                "markdown",
            )
        )
        self.add_button.setMenu(add_menu)
        header.addWidget(self.add_button)

        self.delete_button = QToolButton()
        self.delete_button.setObjectName(
            "CellDeleteButton"
        )
        self.delete_button.setIcon(icon("trash"))
        self.delete_button.setToolTip(
            "Eliminar celda"
        )
        self.delete_button.clicked.connect(
            lambda: self.delete_requested.emit(
                self.cell_id
            )
        )
        header.addWidget(self.delete_button)

        root.addLayout(header)

        for action_button in (
            self.run_button,
            self.add_button,
            self.delete_button,
        ):
            action_button.setVisible(False)

        self.editor = AutoHeightPlainTextEdit(
            minimum_lines=2,
            maximum_lines=12,
        )
        self.editor.setObjectName("CellEditor")
        self.editor.setTabStopDistance(28)

        font = QFont(
            "Cascadia Mono",
            10,
        )
        self.editor.setFont(font)

        self.editor.setPlaceholderText(
            "Escribe código Python…"
            if self.cell_type == "code"
            else "Escribe Markdown…"
        )

        source = cell.get("source") or []
        if isinstance(source, list):
            source = "".join(
                str(part)
                for part in source
            )
        self.editor.setPlainText(str(source))
        self.editor.textChanged.connect(
            self._editor_changed
        )
        self.editor.cursorPositionChanged.connect(
            lambda: self.activated.emit(
                self.cell_id
            )
        )
        root.addWidget(self.editor)

        self.output = AutoHeightPlainTextEdit(
            minimum_lines=1,
            maximum_lines=9,
            read_only=True,
        )
        self.output.setObjectName("CellOutput")
        self.output.setVisible(False)
        root.addWidget(self.output)

        self._render_saved_outputs()
        QTimer.singleShot(
            0,
            self._refresh_heights,
        )

    def _editor_changed(self) -> None:
        self.editor.update_height()
        self.changed.emit()

    def _refresh_heights(self) -> None:
        self.editor.update_height()
        self.output.update_height()

    def _render_saved_outputs(self) -> None:
        chunks: list[str] = []

        for output in self.outputs:
            output_type = output.get(
                "output_type"
            )

            if output_type == "stream":
                text = output.get("text") or ""
                if isinstance(text, list):
                    text = "".join(text)
                chunks.append(str(text))

            elif output_type in {
                "execute_result",
                "display_data",
            }:
                data = output.get("data") or {}
                plain = data.get(
                    "text/plain"
                ) or ""
                if isinstance(plain, list):
                    plain = "".join(plain)
                chunks.append(str(plain))

            elif output_type == "error":
                traceback = output.get(
                    "traceback"
                ) or []
                chunks.append(
                    "\n".join(
                        str(item)
                        for item in traceback
                    )
                )

        rendered = _bounded_output(
            "".join(chunks).strip()
        )
        self.outputs = []

        if rendered:
            self.output.setPlainText(rendered)
            self.output.setVisible(True)
            self.output.update_height()

    def _run(self) -> None:
        self.activated.emit(self.cell_id)
        self.run_requested.emit(
            self.cell_id,
            self.editor.toPlainText(),
        )

    def set_active(self, active: bool) -> None:
        self.setProperty(
            "active",
            active,
        )

        self.run_button.setVisible(
            active
            and self.cell_type == "code"
        )
        self.add_button.setVisible(active)
        self.delete_button.setVisible(active)

        self.style().unpolish(self)
        self.style().polish(self)

    def focus_editor(self) -> None:
        self.editor.setFocus(
            Qt.FocusReason.OtherFocusReason
        )

    def set_result(
        self,
        text: str,
        failed: bool,
        execution_count: int,
    ) -> None:
        self.execution_count = (
            execution_count
            or self.execution_count
        )

        self.exec_label.setText(
            f"[{self.execution_count if self.execution_count is not None else ' '}]:"
        )

        self.output.setProperty(
            "error",
            failed,
        )
        self.output.setPlainText(
            _bounded_output(text)
        )
        self.output.setVisible(bool(text))
        self.output.update_height()
        self.output.style().unpolish(
            self.output
        )
        self.output.style().polish(
            self.output
        )

    def set_busy(self, busy: bool) -> None:
        self.run_button.setEnabled(
            not busy
        )

    def clear_output(self) -> None:
        self.output.clear()
        self.output.hide()

    def to_json(self) -> dict:
        source = self.editor.toPlainText()

        if self.cell_type == "code":
            outputs: list[dict] = []

            if (
                self.output.isVisible()
                and self.output.toPlainText()
            ):
                outputs.append(
                    {
                        "name": "stdout",
                        "output_type": "stream",
                        "text": (
                            self.output.toPlainText()
                            + "\n"
                        ),
                    }
                )

            return {
                "cell_type": "code",
                "execution_count": (
                    self.execution_count
                ),
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
        toolbar.setObjectName(
            "NativeNotebookToolbar"
        )
        row = QHBoxLayout(toolbar)
        row.setContentsMargins(8, 4, 8, 4)
        row.setSpacing(6)

        self.add_code_button = QPushButton(
            "＋ Código"
        )
        self.add_code_button.setObjectName(
            "NotebookToolButton"
        )
        self.add_code_button.clicked.connect(
            self.add_code_cell
        )
        row.addWidget(self.add_code_button)

        self.add_markdown_button = QPushButton(
            "＋ Markdown"
        )
        self.add_markdown_button.setObjectName(
            "NotebookToolButton"
        )
        self.add_markdown_button.clicked.connect(
            self.add_markdown_cell
        )
        row.addWidget(
            self.add_markdown_button
        )

        self.clear_outputs_button = QPushButton(
            "Limpiar salidas"
        )
        self.clear_outputs_button.setObjectName(
            "NotebookToolButton"
        )
        self.clear_outputs_button.clicked.connect(
            self.clear_outputs
        )
        row.addWidget(
            self.clear_outputs_button
        )

        self.delete_cell_button = QPushButton(
            "Eliminar celda"
        )
        self.delete_cell_button.setObjectName(
            "NotebookDeleteButton"
        )
        self.delete_cell_button.setIcon(
            icon("trash")
        )
        self.delete_cell_button.clicked.connect(
            self.delete_active_cell
        )
        row.addWidget(
            self.delete_cell_button
        )

        row.addStretch(1)

        self.kernel_label = QLabel("Python 3")
        self.kernel_label.setObjectName("Muted")
        row.addWidget(self.kernel_label)
        root.addWidget(toolbar)

        self.scroll = QScrollArea()
        self.scroll.setObjectName(
            "NotebookScroll"
        )
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(
            QFrame.Shape.NoFrame
        )
        self.scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.container = QWidget()
        self.container.setObjectName(
            "NotebookCanvas"
        )
        self.cells_layout = QVBoxLayout(
            self.container
        )
        self.cells_layout.setContentsMargins(
            12,
            10,
            12,
            70,
        )
        self.cells_layout.setSpacing(9)
        self.cells_layout.setAlignment(
            Qt.AlignmentFlag.AlignTop
        )

        self.scroll.setWidget(
            self.container
        )
        root.addWidget(
            self.scroll,
            1,
        )

    @property
    def dirty(self) -> bool:
        return self._dirty

    def _set_dirty(
        self,
        value: bool,
    ) -> None:
        if self._dirty == value:
            return

        self._dirty = value
        self.dirty_changed.emit(value)

    def clear(self) -> None:
        for cell in self.cells:
            self.cells_layout.removeWidget(
                cell
            )
            cell.setParent(None)
            cell.deleteLater()

        self.cells.clear()
        self.active_cell_id = None
        self.path = None
        QTimer.singleShot(
            0,
            gc.collect,
        )

    def load_file(self, path: str) -> None:
        target = Path(path).resolve()
        payload = json.loads(
            target.read_text(
                encoding="utf-8"
            )
        )

        self.clear()
        self.path = target
        self.metadata = dict(
            payload.get("metadata")
            or {}
        )
        self.nbformat = int(
            payload.get("nbformat")
            or 4
        )
        self.nbformat_minor = int(
            payload.get("nbformat_minor")
            or 5
        )

        cells = list(
            payload.get("cells")
            or []
        )

        if not cells:
            cells = [
                self._empty_code_cell()
            ]

        for index, cell_data in enumerate(
            cells
        ):
            self._append_cell(
                dict(cell_data),
                index,
            )

        self._set_dirty(False)

        if self.cells:
            self.activate_cell(
                self.cells[0].cell_id
            )
            QTimer.singleShot(
                0,
                self.cells[0].focus_editor,
            )

    @staticmethod
    def _empty_code_cell() -> dict:
        return {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [],
        }

    @staticmethod
    def _empty_markdown_cell() -> dict:
        return {
            "cell_type": "markdown",
            "metadata": {},
            "source": [],
        }

    def _append_cell(
        self,
        cell_data: dict,
        index: int | None = None,
    ) -> NotebookCell:
        insert_at = (
            len(self.cells)
            if index is None
            else max(
                0,
                min(index, len(self.cells)),
            )
        )

        cell = NotebookCell(
            cell_data,
            insert_at,
        )
        cell.run_requested.connect(
            self.execute_requested.emit
        )
        cell.activated.connect(
            self.activate_cell
        )
        cell.changed.connect(
            lambda: self._set_dirty(True)
        )
        cell.insert_below_requested.connect(
            self.insert_cell_below
        )
        cell.delete_requested.connect(
            self.delete_cell
        )

        self.cells.insert(
            insert_at,
            cell,
        )
        self.cells_layout.insertWidget(
            insert_at,
            cell,
        )
        return cell

    def _active_index(self) -> int:
        for index, cell in enumerate(
            self.cells
        ):
            if (
                cell.cell_id
                == self.active_cell_id
            ):
                return index

        return len(self.cells) - 1

    def _insert_after_active(
        self,
        cell_data: dict,
    ) -> NotebookCell:
        active_index = self._active_index()
        insert_at = (
            active_index + 1
            if self.cells
            else 0
        )

        cell = self._append_cell(
            cell_data,
            insert_at,
        )

        self._set_dirty(True)
        self.activate_cell(cell.cell_id)
        QTimer.singleShot(
            0,
            cell.focus_editor,
        )
        QTimer.singleShot(
            0,
            lambda: self.scroll.ensureWidgetVisible(
                cell,
                24,
                40,
            ),
        )
        return cell

    def add_code_cell(self) -> None:
        self._insert_after_active(
            self._empty_code_cell()
        )

    def add_markdown_cell(self) -> None:
        self._insert_after_active(
            self._empty_markdown_cell()
        )

    def insert_cell_below(
        self,
        cell_id: str,
        cell_type: str = "code",
    ) -> None:
        self.activate_cell(cell_id)

        if cell_type == "markdown":
            self.add_markdown_cell()
        else:
            self.add_code_cell()

    def delete_active_cell(self) -> None:
        cell = self.active_cell()

        if cell:
            self.delete_cell(
                cell.cell_id
            )

    def delete_cell(
        self,
        cell_id: str,
    ) -> None:
        index = next(
            (
                index
                for index, cell in enumerate(
                    self.cells
                )
                if cell.cell_id == cell_id
            ),
            -1,
        )

        if index < 0:
            return

        cell = self.cells.pop(index)
        self.cells_layout.removeWidget(cell)
        cell.setParent(None)
        cell.deleteLater()
        QTimer.singleShot(
            0,
            gc.collect,
        )

        if not self.cells:
            replacement = self._append_cell(
                self._empty_code_cell(),
                0,
            )
            next_cell = replacement
        else:
            next_cell = self.cells[
                min(
                    index,
                    len(self.cells) - 1,
                )
            ]

        self._set_dirty(True)
        self.activate_cell(
            next_cell.cell_id
        )
        QTimer.singleShot(
            0,
            next_cell.focus_editor,
        )

    def activate_cell(
        self,
        cell_id: str,
    ) -> None:
        self.active_cell_id = cell_id

        for cell in self.cells:
            cell.set_active(
                cell.cell_id == cell_id
            )

        self.active_cell_changed.emit(
            cell_id
        )

    def active_cell(
        self,
    ) -> NotebookCell | None:
        for cell in self.cells:
            if (
                cell.cell_id
                == self.active_cell_id
            ):
                return cell

        return (
            self.cells[0]
            if self.cells
            else None
        )

    def set_execution_busy(
        self,
        busy: bool,
    ) -> None:
        # Execution happens in the kernel process, not the Qt UI. Keep cell
        # creation/editing available while Python is busy; only prevent a
        # second execution from the same cell.
        for cell in self.cells:
            cell.set_busy(busy)

    def clear_outputs(self) -> None:
        for cell in self.cells:
            cell.clear_output()

        self._set_dirty(True)
        QTimer.singleShot(
            0,
            gc.collect,
        )

    def execute_active(self) -> None:
        cell = self.active_cell()

        if (
            not cell
            or cell.cell_type != "code"
        ):
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
                cell.set_result(
                    text,
                    failed,
                    execution_count,
                )
                self._set_dirty(True)
                QTimer.singleShot(
                    0,
                    lambda current=cell: self.scroll.ensureWidgetVisible(
                        current,
                        20,
                        36,
                    ),
                )
                return

    def save(self) -> None:
        if self.path is None:
            return

        payload = {
            "cells": [
                cell.to_json()
                for cell in self.cells
            ],
            "metadata": self.metadata,
            "nbformat": self.nbformat,
            "nbformat_minor": (
                self.nbformat_minor
            ),
        }

        self.path.write_text(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=1,
            )
            + "\n",
            encoding="utf-8",
        )
        self._set_dirty(False)
