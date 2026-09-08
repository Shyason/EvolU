from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon, QPainter, QPixmap


def render_emoji_icon(emoji: str, size: int = 24) -> QIcon:
    """Draws an emoji character onto a transparent pixmap using a font that
    actually supports color emoji glyphs, then wraps it as a QIcon. This
    avoids relying on QSS/font-cascade to render emoji correctly inside
    styled widgets, which is unreliable on Windows with Qt's Fusion style."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    font = QFont("Segoe UI Emoji")
    font.setPixelSize(int(size * 0.75))
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, emoji)
    painter.end()

    return QIcon(pixmap)