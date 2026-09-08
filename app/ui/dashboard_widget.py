from __future__ import annotations

import datetime as dt

from PySide6.QtCore import Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.business.gamification_events import XP_PER_HABIT, XP_PER_TASK
from app.business.gamification_service import GamificationService
from app.business.scheduling import describe_recurrence, is_habit_due_on
from app.business.streak_engine import calculate_current_streak, calculate_longest_streak
from app.data.repository import (
    HabitCompletionRepository,
    HabitRepository,
    ProfileRepository,
    TaskRepository,
)
from app.ui.emoji_icon import render_emoji_icon
from app.ui.habit_heatmap_dialog import HabitHeatmapDialog
from app.ui.progress_ring_widget import ProgressRingWidget
from app.ui.emoji_icon import render_emoji_icon

class DashboardRow(QWidget):
    toggled = Signal(str, int, bool)
    view_history_requested = Signal(int)

    def __init__(self, item_type, item_id, title, tag_color, is_checked, streak=None, subtitle=None):
        super().__init__()
        self.setObjectName("card")
        self.item_type = item_type
        self.item_id = item_id

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(18)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 14)
        outer.setSpacing(14)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(is_checked)
        self.checkbox.stateChanged.connect(self._on_toggled)
        outer.addWidget(self.checkbox)

        accent_strip = QLabel()
        accent_strip.setFixedSize(4, 34)
        accent_strip.setStyleSheet("background-color: " + tag_color + "; border-radius: 2px;")
        outer.addWidget(accent_strip)

        text_column = QVBoxLayout()
        text_column.setSpacing(2)

        title_row = QHBoxLayout()
        title_row.setSpacing(6)

        type_icon = QLabel("\U0001F501" if item_type == "habit" else "\U0001F4CC")
        type_icon.setProperty("class", "emoji")
        type_icon.style().unpolish(type_icon)
        type_icon.style().polish(type_icon)

        title_label = QLabel(title)
        title_label.setProperty("class", "title")
        self.title_label = title_label

        title_row.addWidget(type_icon)
        title_row.addWidget(title_label, 1)
        text_column.addLayout(title_row)

        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setProperty("class", "caption")
            text_column.addWidget(subtitle_label)

        outer.addLayout(text_column, 1)

        if item_type == "habit" and streak is not None:
            streak_pill = QLabel("\U0001F525 " + str(streak))
            streak_pill.setStyleSheet(
                "background-color: rgba(34, 197, 94, 0.15); color: #22C55E;"
                "border-radius: 12px; padding: 4px 10px; font-weight: 600; font-size: 12px;"
            )
            outer.addWidget(streak_pill)

            history_button = QPushButton()
            history_button.setIcon(render_emoji_icon("\U0001F4CA"))
            history_button.setFixedWidth(32)
            history_button.clicked.connect(lambda: self.view_history_requested.emit(self.item_id))
            outer.addWidget(history_button)

        self._apply_completed_style(is_checked)

    def _apply_completed_style(self, is_checked):
        strike = "text-decoration: line-through; color: gray;" if is_checked else ""
        self.title_label.setStyleSheet(strike)

    def _on_toggled(self, state):
        is_checked = bool(state)
        self._apply_completed_style(is_checked)
        self.toggled.emit(self.item_type, self.item_id, is_checked)


class DashboardWidget(QWidget):
    data_changed = Signal()
    xp_changed = Signal()

    def __init__(self):
        super().__init__()
        self.task_repo = TaskRepository()
        self.habit_repo = HabitRepository()
        self.completion_repo = HabitCompletionRepository()
        self.profile_repo = ProfileRepository()
        self.gamification_service = GamificationService()
        self.current_profile_id = None

        self.layout_ = QVBoxLayout(self)

        header_row = QHBoxLayout()

        greeting_column = QVBoxLayout()
        greeting_column.setSpacing(2)

        greeting_row = QHBoxLayout()
        greeting_row.setSpacing(8)

        self.greeting_label = QLabel("Hello!")
        self.greeting_label.setProperty("class", "heading")
        greeting_row.addWidget(self.greeting_label)

        self.greeting_emoji = QLabel()
        self.greeting_emoji.setPixmap(render_emoji_icon("\U0001F44B", size=32).pixmap(32, 32))
        greeting_row.addWidget(self.greeting_emoji)
        greeting_row.addStretch()

        greeting_column.addLayout(greeting_row)

        self.date_label = QLabel("")
        self.date_label.setStyleSheet("color: #94A3B8; font-size: 14px;")
        greeting_column.addWidget(self.date_label)

        header_row.addLayout(greeting_column, 1)

        self.progress_ring = ProgressRingWidget()
        header_row.addWidget(self.progress_ring)
        self.layout_.addLayout(header_row)

        self.rows_container = QVBoxLayout()
        self.rows_container.setSpacing(10)
        self.layout_.addLayout(self.rows_container)
        self.layout_.addStretch()

        self.empty_label = QLabel("Nothing due today.")
        self.layout_.addWidget(self.empty_label)
        self.empty_label.hide()

    def load_for_profile(self, profile_id):
        self.current_profile_id = profile_id
        self.refresh()

    def _greeting_prefix(self):
        hour = dt.datetime.now().hour
        if hour < 12:
            return "Good morning"
        if hour < 18:
            return "Good afternoon"
        return "Good evening"

    def refresh(self):
        while self.rows_container.count():
            item = self.rows_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if self.current_profile_id is None:
            return

        profile = self.profile_repo.get_by_id(self.current_profile_id)
        if profile:
            self.greeting_label.setText(self._greeting_prefix() + ", " + profile.name)
        today = dt.date.today()
        self.date_label.setText(today.strftime("%A, %b ") + str(today.day))

        row_count = 0
        total_items = 0
        completed_items = 0

        for habit in self.habit_repo.get_all(self.current_profile_id):
            if not is_habit_due_on(habit, today):
                continue
            tag_color = habit.tag.color_hex if habit.tag else "#888888"
            is_done = self.completion_repo.is_complete_on(habit.id, today)
            recurrence_desc = describe_recurrence(habit.recurrence_type, habit.recurrence_params)
            row = DashboardRow(
                "habit", habit.id, habit.title, tag_color, is_done,
                streak=habit.current_streak, subtitle=recurrence_desc,
            )
            row.toggled.connect(self._on_row_toggled)
            row.view_history_requested.connect(self._on_view_history_requested)
            self.rows_container.addWidget(row)
            row_count += 1
            total_items += 1
            if is_done:
                completed_items += 1

        today_tasks = self.task_repo.get_today(self.current_profile_id, today)
        priority_order = {"high": 0, "medium": 1, "low": 2}
        today_tasks.sort(key=lambda t: (t.is_completed, priority_order.get(t.priority, 1)))

        for task in today_tasks:
            tag_color = task.tag.color_hex if task.tag else "#888888"
            time_part = task.due_time.strftime("%I:%M %p").lstrip("0") if task.due_time else None
            priority_part = task.priority.capitalize() + " priority"
            subtitle = (time_part + "  \u00b7  " + priority_part) if time_part else priority_part
            row = DashboardRow("task", task.id, task.title, tag_color, task.is_completed, subtitle=subtitle)
            row.toggled.connect(self._on_row_toggled)
            self.rows_container.addWidget(row)
            row_count += 1
            total_items += 1
            if task.is_completed:
                completed_items += 1

        self.empty_label.setVisible(row_count == 0)
        percent = (completed_items / total_items * 100) if total_items > 0 else 0
        self.progress_ring.set_percent(percent)

    def _on_row_toggled(self, item_type, item_id, is_checked):
        if item_type == "task":
            self.task_repo.toggle_complete(item_id)
            if is_checked:
                self.gamification_service.award_for_task_completion(self.current_profile_id)
            else:
                self.gamification_service.revert_for_uncomplete(self.current_profile_id, XP_PER_TASK)
            self.xp_changed.emit()
            self.refresh()
            self.data_changed.emit()
            return

        today = dt.date.today()
        if is_checked:
            self.completion_repo.mark_complete(item_id)
            self.gamification_service.award_for_habit_completion(self.current_profile_id)
        else:
            self.completion_repo.delete_for_date(item_id, today)
            self.gamification_service.revert_for_uncomplete(self.current_profile_id, XP_PER_HABIT)

        self._recalculate_streak(item_id)
        self.xp_changed.emit()
        self.refresh()
        self.data_changed.emit()

    def _recalculate_streak(self, habit_id):
        habit = self.habit_repo.get_by_id(habit_id)
        completed_dates = {c.date for c in habit.completions}
        current = calculate_current_streak(habit, completed_dates, dt.date.today())
        longest = max(calculate_longest_streak(habit, completed_dates), current)
        self.habit_repo.update_streaks(habit_id, current, longest)

    def _on_view_history_requested(self, habit_id):
        dialog = HabitHeatmapDialog(habit_id, self)
        dialog.exec()
