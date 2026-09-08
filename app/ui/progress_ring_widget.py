from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget


class ProgressRingWidget(QWidget):
    def __init__(self, size=90):
        super().__init__()
        self.setFixedSize(size, size)
        self._percent = 0

    def set_percent(self, percent):
        self._percent = max(0, min(100, percent))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(6, 6, -6, -6)

        bg_pen = QPen(QColor("#2A3752"), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(bg_pen)
        painter.drawArc(rect, 0, 360 * 16)

        fg_pen = QPen(QColor("#22C55E"), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(fg_pen)
        span_angle = int(360 * 16 * (self._percent / 100))
        painter.drawArc(rect, 90 * 16, -span_angle)

        painter.setPen(QColor("#F3F4F6"))
        font = QFont("Plus Jakarta Sans")
        font.setPointSize(14)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"{int(self._percent)}%")

        painter.end()
