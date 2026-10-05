from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QSize, QVariantAnimation
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QPushButton,
    QToolButton,
    QWidget,
)


class _IconPulseMixin:
    def _setup_icon_pulse(self, base: int = 18, hover: int = 20) -> None:
        self._base_icon_size = base
        self._hover_icon_size = hover
        self.setIconSize(QSize(base, base))

        self._icon_animation = QVariantAnimation(self)
        self._icon_animation.setDuration(120)
        self._icon_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._icon_animation.valueChanged.connect(self._apply_icon_size)

    def _apply_icon_size(self, value) -> None:
        size = max(1, int(round(float(value))))
        self.setIconSize(QSize(size, size))

    def _animate_icon_to(self, target: int) -> None:
        if self.icon().isNull():
            return
        self._icon_animation.stop()
        self._icon_animation.setStartValue(self.iconSize().width())
        self._icon_animation.setEndValue(target)
        self._icon_animation.start()

    def enterEvent(self, event) -> None:
        self._animate_icon_to(self._hover_icon_size)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._animate_icon_to(self._base_icon_size)
        super().leaveEvent(event)


class AnimatedToolButton(_IconPulseMixin, QToolButton):
    def __init__(self, parent=None, *, base_icon: int = 18, hover_icon: int = 20):
        super().__init__(parent)
        self._setup_icon_pulse(base_icon, hover_icon)


class AnimatedPushButton(_IconPulseMixin, QPushButton):
    def __init__(self, text: str = "", parent=None, *, base_icon: int = 17, hover_icon: int = 19):
        super().__init__(text, parent)
        self._setup_icon_pulse(base_icon, hover_icon)


def add_soft_shadow(
    widget: QWidget,
    *,
    blur: int = 18,
    y_offset: int = 3,
    alpha: int = 28,
) -> None:
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setOffset(0, y_offset)
    shadow.setColor(QColor(31, 74, 110, alpha))
    widget.setGraphicsEffect(shadow)
