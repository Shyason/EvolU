from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.data.repository import NotificationLogRepository
from app.ui.emoji_icon import render_emoji_icon


class NotificationHistoryDialog(QDialog):
    def __init__(self, profile_id: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Notifications")
        self.setMinimumWidth(400)
        self.log_repo = NotificationLogRepository()
        self.profile_id = profile_id

        layout = QVBoxLayout(self)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)

        logs = self.log_repo.get_all(profile_id)
        logs.sort(key=lambda log: log.triggered_at, reverse=True)

        if not logs:
            content_layout.addWidget(QLabel("No notifications yet."))
        else:
            for log in logs:
                time_str = log.triggered_at.strftime("%b %d, %I:%M %p").replace(" 0", " ")
                entry = QLabel(f"<b>{time_str}</b><br>{log.message}")
                entry.setStyleSheet("padding: 6px; border-bottom: 1px solid #333;")
                content_layout.addWidget(entry)
                if not log.was_seen:
                    self.log_repo.mark_seen(log.id)

        content_layout.addStretch()
        scroll_area.setWidget(content)
        layout.addWidget(scroll_area)


class NotificationBell(QWidget):
    def __init__(self):
        super().__init__()
        self.log_repo = NotificationLogRepository()
        self.current_profile_id: int | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.button = QPushButton()
        self.button.setIcon(render_emoji_icon("🔔"))
        self.button.setFixedWidth(40)
        self.button.clicked.connect(self._open_history)
        layout.addWidget(self.button)

    def set_profile(self, profile_id: int) -> None:
        self.current_profile_id = profile_id
        self.refresh_count()

    def refresh_count(self) -> None:
        if self.current_profile_id is None:
            return
        unseen = self.log_repo.get_unseen(self.current_profile_id)
        self.button.setText(f" {len(unseen)}" if unseen else "")

    def _open_history(self) -> None:
        if self.current_profile_id is None:
            return
        dialog = NotificationHistoryDialog(self.current_profile_id, self)
        dialog.exec()
        self.refresh_count()