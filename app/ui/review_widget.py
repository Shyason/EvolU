from __future__ import annotations

import datetime as dt

from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from app.business.review import build_daily_review, build_weekly_review
from app.data.repository import HabitCompletionRepository, HabitRepository, TaskRepository


class ReviewWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.task_repo = TaskRepository()
        self.habit_repo = HabitRepository()
        self.completion_repo = HabitCompletionRepository()
        self.current_profile_id: int | None = None
        self.mode = "daily"

        outer_layout = QVBoxLayout(self)
        outer_layout.addWidget(QLabel("<h2>Review</h2>"))

        mode_row = QHBoxLayout()
        self.daily_button = QPushButton("Daily")
        self.weekly_button = QPushButton("Weekly")
        for button in (self.daily_button, self.weekly_button):
            button.setCheckable(True)
        self.daily_button.setChecked(True)
        self.daily_button.clicked.connect(lambda: self._set_mode("daily"))
        self.weekly_button.clicked.connect(lambda: self._set_mode("weekly"))
        mode_row.addWidget(self.daily_button)
        mode_row.addWidget(self.weekly_button)
        mode_row.addStretch()
        outer_layout.addLayout(mode_row)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.addStretch()
        scroll_area.setWidget(self.content)
        outer_layout.addWidget(scroll_area, stretch=1)

    def load_for_profile(self, profile_id: int) -> None:
        self.current_profile_id = profile_id
        self.refresh()

    def _set_mode(self, mode: str) -> None:
        self.mode = mode
        self.daily_button.setChecked(mode == "daily")
        self.weekly_button.setChecked(mode == "weekly")
        self.refresh()

    def refresh(self) -> None:
        while self.content_layout.count() > 1:
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if self.current_profile_id is None:
            return

        tasks = self.task_repo.get_all(self.current_profile_id)
        habits = self.habit_repo.get_all(self.current_profile_id)
        completions_by_habit = {
            habit.id: {c.date for c in self.completion_repo.get_for_habit(habit.id)}
            for habit in habits
        }

        if self.mode == "daily":
            self._render_daily(tasks, habits, completions_by_habit)
        else:
            self._render_weekly(tasks, habits, completions_by_habit)

    def _add_line(self, text: str, bold: bool = False, color: str | None = None) -> None:
        label = QLabel(text)
        style_parts = []
        if bold:
            style_parts.append("font-weight: bold;")
        if color:
            style_parts.append(f"color: {color};")
        if style_parts:
            label.setStyleSheet(" ".join(style_parts))
        self.content_layout.insertWidget(self.content_layout.count() - 1, label)

    def _render_daily(self, tasks, habits, completions_by_habit) -> None:
        review = build_daily_review(tasks, habits, completions_by_habit, dt.date.today())

        self._add_line(f"<h3>{review.date.strftime('%A, %B %d')}</h3>", bold=True)
        self._add_line(f"Tasks: {review.tasks_completed} / {review.tasks_total} completed today")
        self._add_line(f"Habits: {review.habits_completed} / {review.habits_due} completed today")

        if review.overdue_task_titles:
            self._add_line(" ")
            self._add_line("Overdue:", bold=True, color="#e05252")
            for title in review.overdue_task_titles:
                self._add_line(f"  • {title}", color="#e05252")

        if review.habit_streaks:
            self._add_line(" ")
            self._add_line("Current streaks:", bold=True)
            for title, streak in sorted(review.habit_streaks, key=lambda pair: pair[1], reverse=True):
                self._add_line(f"  🔥 {title}: {streak}")

    def _render_weekly(self, tasks, habits, completions_by_habit) -> None:
        review = build_weekly_review(tasks, habits, completions_by_habit, dt.date.today())

        range_str = f"{review.start_date.strftime('%b %d')} – {review.end_date.strftime('%b %d')}"
        self._add_line(f"<h3>Week of {range_str}</h3>", bold=True)
        self._add_line(f"Tasks: {review.tasks_completed} / {review.tasks_total} completed this week")

        if review.habit_completion_rate is not None:
            rate_pct = round(review.habit_completion_rate * 100)
            self._add_line(f"Habit completion rate: {rate_pct}% ({review.missed_habit_days} missed day(s))")
        else:
            self._add_line("No habits were scheduled this week.")

        if review.best_habit:
            self._add_line(" ")
            self._add_line(f"Best streak: {review.best_habit[0]} 🔥 {review.best_habit[1]}", color="#39d353")
        if review.worst_habit and review.worst_habit != review.best_habit:
            self._add_line(f"Needs attention: {review.worst_habit[0]} 🔥 {review.worst_habit[1]}", color="#e05252")