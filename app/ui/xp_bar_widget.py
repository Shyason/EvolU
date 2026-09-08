from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QVBoxLayout, QWidget

from app.business.gamification import get_level_progress
from app.data.repository import ProfileRepository


class XPBarWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.profile_repo = ProfileRepository()
        self.current_profile_id: int | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.level_badge = QLabel("Lv 1")
        self.level_badge.setStyleSheet(
            "background-color: rgba(255, 176, 32, 0.15); color: #ffb020;"
            "border-radius: 12px; padding: 4px 12px; font-weight: 700; font-size: 12px;"
        )
        layout.addWidget(self.level_badge)

        bar_column = QVBoxLayout()
        bar_column.setSpacing(2)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(
            "QProgressBar { background-color: rgba(255,255,255,0.08); border-radius: 4px; }"
            "QProgressBar::chunk { background-color: #ffb020; border-radius: 4px; }"
        )
        bar_column.addWidget(self.progress_bar)

        self.xp_label = QLabel("0 / 100 XP")
        self.xp_label.setProperty("class", "caption")
        bar_column.addWidget(self.xp_label)

        layout.addLayout(bar_column, stretch=1)
        self.setFixedWidth(180)

    def set_profile(self, profile_id: int) -> None:
        self.current_profile_id = profile_id
        self.refresh()

    def refresh(self) -> None:
        if self.current_profile_id is None:
            return
        profile = self.profile_repo.get_by_id(self.current_profile_id)
        if profile is None:
            return

        progress = get_level_progress(profile.xp)
        self.level_badge.setText(f"Lv {progress.level}")
        self.progress_bar.setRange(0, progress.xp_needed_for_level)
        self.progress_bar.setValue(progress.xp_into_level)
        self.xp_label.setText(f"{progress.xp_into_level} / {progress.xp_needed_for_level} XP")