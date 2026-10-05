from __future__ import annotations

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTreeView,
)


class CleanProjectTree(QTreeView):
    """Project tree with branches painted by Archyter, not the native style.

    On some Windows/Qt style combinations the native branch primitive can
    render as a solid black/blue/red rectangle. Drawing the chevron ourselves
    keeps the indentation area deterministic on every Windows theme.
    """

    def drawBranches(self, painter: QPainter, rect: QRect, index) -> None:
        model = self.model()
        if model is None or not index.isValid():
            return

        try:
            is_dir = bool(model.isDir(index))
            has_children = bool(model.hasChildren(index))
        except Exception:
            return

        if not is_dir or not has_children:
            return

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        pen = QPen(QColor("#52667c"))
        pen.setWidthF(1.7)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        center_x = rect.right() - 7
        center_y = rect.center().y()

        if self.isExpanded(index):
            painter.drawLine(center_x - 4, center_y - 2, center_x, center_y + 2)
            painter.drawLine(center_x, center_y + 2, center_x + 4, center_y - 2)
        else:
            painter.drawLine(center_x - 2, center_y - 4, center_x + 2, center_y)
            painter.drawLine(center_x + 2, center_y, center_x - 2, center_y + 4)

        painter.restore()


class CleanTreeDelegate(QStyledItemDelegate):
    """Stable row painter that keeps selection away from the branch gutter."""

    def paint(self, painter: QPainter, option, index) -> None:
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        selected = bool(opt.state & QStyle.StateFlag.State_Selected)
        hovered = bool(opt.state & QStyle.StateFlag.State_MouseOver)

        row_rect = opt.rect.adjusted(2, 2, -3, -2)

        if selected:
            painter.setPen(QPen(QColor("#a7d2f5"), 1.0))
            painter.setBrush(QColor("#dceeff"))
            painter.drawRoundedRect(row_rect, 6, 6)
        elif hovered:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#eff6fd"))
            painter.drawRoundedRect(row_rect, 6, 6)

        icon_rect = QRect(
            row_rect.left() + 7,
            row_rect.top() + max(0, (row_rect.height() - 18) // 2),
            18,
            18,
        )

        if not opt.icon.isNull():
            pixmap = opt.icon.pixmap(
                QSize(18, 18),
                self._icon_mode(opt),
                self._icon_state(opt),
            )
            if not pixmap.isNull():
                painter.drawPixmap(icon_rect, pixmap)

        text_left = icon_rect.right() + 7
        text_rect = QRect(
            text_left,
            row_rect.top(),
            max(0, row_rect.right() - text_left - 5),
            row_rect.height(),
        )

        painter.setPen(QColor("#075b9b") if selected else QColor("#314158"))
        font = opt.font
        font.setBold(selected)
        painter.setFont(font)
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            opt.text,
        )

        painter.restore()

    def sizeHint(self, option, index) -> QSize:
        size = super().sizeHint(option, index)
        size.setHeight(max(27, size.height()))
        return size

    @staticmethod
    def _icon_mode(option: QStyleOptionViewItem):
        if not (option.state & QStyle.StateFlag.State_Enabled):
            from PySide6.QtGui import QIcon
            return QIcon.Mode.Disabled
        from PySide6.QtGui import QIcon
        return QIcon.Mode.Normal

    @staticmethod
    def _icon_state(option: QStyleOptionViewItem):
        from PySide6.QtGui import QIcon
        if option.state & QStyle.StateFlag.State_Open:
            return QIcon.State.On
        return QIcon.State.Off
