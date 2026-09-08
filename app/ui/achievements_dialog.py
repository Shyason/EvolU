from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.data.achievement_repository import AchievementRepository


class AchievementCard(QWidget):
    def __init__(self, icon: str, title: str, description: str, is_unlocked: bool, unlocked_at_text: str | None):
        super().__init__()
        self.setObjectName("card")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(14)

        icon_label = QLabel(icon)
        icon_label.setProperty("class", "emoji")
        icon_label.setFixedWidth(36)
        icon_label.setStyleSheet("font-size: 24px;")
        layout.addWidget(icon_label)

        text_column = QVBoxLayout()
        text_column.setSpacing(2)

        title_label = QLabel(title)
        title_label.setProperty("class", "title")
        text_column.addWidget(title_label)

        description_label = QLabel(description)
        description_label.setProperty("class", "caption")
        description_label.setWordWrap(True)
        text_column.addWidget(description_label)

        layout.addLayout(text_column, stretch=1)

        if is_unlocked:
            status_label = QLabel(f"Unlocked\n{unlocked_at_text}")
            status_label.setStyleSheet(
                "background-color: rgba(255, 176, 32, 0.15); color: #ffb020;"
                "border-radius: 10px; padding: 6px 12px; font-weight: 600; font-size: 11px;"
            )
        else:
            status_label = QLabel("Locked")
            status_label.setStyleSheet(
                "background-color: rgba(255,255,255,0.06); color: #5c5d6d;"
                "border-radius: 10px; padding: 6px 12px; font-weight: 600; font-size: 11px;"
            )
        layout.addWidget(status_label)

        if not is_unlocked:
            icon_label.setStyleSheet("font-size: 24px; color: #5c5d6d;")
            title_label.setStyleSheet("color: #5c5d6d;")


class AchievementsDialog(QDialog):
    def __init__(self, profile_id: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Achievements")
        self.setMinimumSize(480, 560)
        self.achievement_repo = AchievementRepository()

        layout = QVBoxLayout(self)
        heading = QLabel("Achievements")
        heading.setProperty("class", "heading")
        layout.addWidget(heading)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(10)

        all_achievements = self.achievement_repo.get_all()
        unlocked = {
            u.achievement.code: u.unlocked_at
            for u in self.achievement_repo.get_unlocked_with_details(profile_id)
        }

        # Unlocked achievements first, so your earned progress is what you see immediately.
        sorted_achievements = sorted(all_achievements, key=lambda a: a.code not in unlocked)

        unlocked_count = len(unlocked)
        total_count = len(all_achievements)
        progress_label = QLabel(f"{unlocked_count} / {total_count} unlocked")
        progress_label.setProperty("class", "caption")
        layout.addWidget(progress_label)

        for achievement in sorted_achievements:
            is_unlocked = achievement.code in unlocked
            unlocked_at_text = (
                unlocked[achievement.code].strftime("%b %d, %Y") if is_unlocked else None
            )
            card = AchievementCard(
                achievement.icon, achievement.title, achievement.description,
                is_unlocked, unlocked_at_text,
            )
            content_layout.addWidget(card)

        content_layout.addStretch()
        scroll_area.setWidget(content)
        layout.addWidget(scroll_area, stretch=1)