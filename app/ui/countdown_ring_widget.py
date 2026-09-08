from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget


class CountdownRingWidget(QWidget):
    def __init__(self, size=160):
        super().__init__()
        self.setFixedSize(size, size)
        self._fraction_remaining = 1.0
        self._time_text = "00:00"

    def set_state(self, fraction_remaining, time_text):
        self._fraction_remaining = max(0.0, min(1.0, fraction_remaining))
        self._time_text = time_text
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(8, 8, -8, -8)

        bg_pen = QPen(QColor("#2A3752"), 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(bg_pen)
        painter.drawArc(rect, 0, 360 * 16)

        fg_pen = QPen(QColor("#22C55E"), 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(fg_pen)
        span_angle = int(360 * 16 * self._fraction_remaining)
        painter.drawArc(rect, 90 * 16, -span_angle)

        painter.setPen(QColor("#F3F4F6"))
        font = QFont("Plus Jakarta Sans")
        font.setPointSize(20)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._time_text)

        painter.end()
