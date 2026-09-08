from __future__ import annotations

import datetime as dt

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

from PySide6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget

from app.business.analytics import (
    calculate_daily_completion_rates,
    get_completed_tasks_by_tag,
    get_streak_comparison,
)
from app.data.repository import (
    HabitCompletionRepository,
    HabitRepository,
    ProfileRepository,
    TaskRepository,
)
from app.ui.theme import DARK, LIGHT

TAG_COLORS = ["#5b6ef5", "#8b5cf6", "#ec4899", "#14b8a6", "#34d399", "#f97316"]


class AnalyticsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.habit_repo = HabitRepository()
        self.completion_repo = HabitCompletionRepository()
        self.task_repo = TaskRepository()
        self.profile_repo = ProfileRepository()
        self.current_profile_id = None

        outer_layout = QVBoxLayout(self)
        outer_layout.addWidget(QLabel("<h2>Analytics</h2>"))

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        scroll_area.setWidget(content)
        outer_layout.addWidget(scroll_area, stretch=1)

        self.completion_figure = Figure(figsize=(6, 3))
        self.completion_canvas = FigureCanvasQTAgg(self.completion_figure)

        self.streak_figure = Figure(figsize=(6, 3))
        self.streak_canvas = FigureCanvasQTAgg(self.streak_figure)

        self.tag_figure = Figure(figsize=(6, 3))
        self.tag_canvas = FigureCanvasQTAgg(self.tag_figure)

        for canvas in (self.completion_canvas, self.streak_canvas, self.tag_canvas):
            self.content_layout.addWidget(canvas)

        self.empty_label = QLabel("Add some habits and tasks to see analytics here.")
        self.content_layout.addWidget(self.empty_label)
        self.empty_label.hide()

    def load_for_profile(self, profile_id):
        self.current_profile_id = profile_id
        self.refresh()

    def _current_palette(self):
        if self.current_profile_id is None:
            return DARK
        profile = self.profile_repo.get_by_id(self.current_profile_id)
        if profile is None:
            return DARK
        return DARK if profile.is_dark_mode else LIGHT

    def refresh(self):
        if self.current_profile_id is None:
            return

        p = self._current_palette()

        habits = self.habit_repo.get_all(self.current_profile_id)
        tasks = self.task_repo.get_all(self.current_profile_id)

        has_data = bool(habits) or bool(tasks)
        self.empty_label.setVisible(not has_data)
        for canvas in (self.completion_canvas, self.streak_canvas, self.tag_canvas):
            canvas.setVisible(has_data)
        if not has_data:
            return

        self._draw_completion_chart(habits, p)
        self._draw_streak_chart(habits, p)
        self._draw_tag_chart(tasks, p)

    def _style_figure_and_axes(self, figure, ax, p):
        figure.set_facecolor(p.bg_surface)
        ax.set_facecolor(p.bg_surface)
        ax.tick_params(colors=p.text_secondary, labelsize=8)
        for spine in ax.spines.values():
            spine.set_color(p.border)
        ax.title.set_color(p.text_primary)
        ax.title.set_fontweight("bold")
        ax.xaxis.label.set_color(p.text_secondary)
        ax.yaxis.label.set_color(p.text_secondary)
        ax.grid(True, color=p.border, linewidth=0.6, alpha=0.5)
        ax.set_axisbelow(True)

    def _draw_completion_chart(self, habits, p):
        completions_by_habit = {
            habit.id: {c.date for c in self.completion_repo.get_for_habit(habit.id)}
            for habit in habits
        }
        rates = calculate_daily_completion_rates(habits, completions_by_habit, days=30, end_date=dt.date.today())

        self.completion_figure.clear()
        ax = self.completion_figure.add_subplot(111)
        self._style_figure_and_axes(self.completion_figure, ax, p)
        ax.set_title("Habit completion rate - last 30 days", fontsize=10)

        dates = [d for d, rate in rates if rate is not None]
        values = [rate * 100 for d, rate in rates if rate is not None]
        if dates:
            ax.plot(dates, values, color=p.primary, marker="o", markersize=3, linewidth=2)
            ax.fill_between(dates, values, color=p.primary, alpha=0.15)
            ax.set_ylim(0, 105)
            ax.set_ylabel("% completed")
            self.completion_figure.autofmt_xdate(rotation=30)
        else:
            ax.text(0.5, 0.5, "No scheduled habit-days in this range", ha="center",
                    color=p.text_secondary, transform=ax.transAxes)

        self.completion_figure.tight_layout()
        self.completion_canvas.draw()

    def _draw_streak_chart(self, habits, p):
        comparison = get_streak_comparison(habits)

        self.streak_figure.clear()
        ax = self.streak_figure.add_subplot(111)
        self._style_figure_and_axes(self.streak_figure, ax, p)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.set_title("Current streak by habit", fontsize=10)

        if comparison:
            titles = [title for title, _ in comparison]
            streaks = [streak for _, streak in comparison]
            colors = [p.success if s > 0 else p.danger for s in streaks]
            ax.barh(titles, streaks, color=colors, height=0.55)
            ax.set_xlabel("Days")
            ax.set_xlim(0, max(streaks + [3]))
            ax.invert_yaxis()
        else:
            ax.text(0.5, 0.5, "No habits yet", ha="center", color=p.text_secondary, transform=ax.transAxes)

        self.streak_figure.tight_layout()
        self.streak_canvas.draw()

    def _draw_tag_chart(self, tasks, p):
        counts = get_completed_tasks_by_tag(tasks)

        self.tag_figure.clear()
        ax = self.tag_figure.add_subplot(111)
        self._style_figure_and_axes(self.tag_figure, ax, p)
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax.set_title("Completed tasks by tag", fontsize=10)

        if counts:
            tags = list(counts.keys())
            values = list(counts.values())
            colors = [TAG_COLORS[i % len(TAG_COLORS)] for i in range(len(tags))]
            ax.bar(tags, values, color=colors, width=0.55)
            ax.set_ylabel("Completed tasks")
            self.tag_figure.autofmt_xdate(rotation=20)
        else:
            ax.text(0.5, 0.5, "No completed tasks yet", ha="center", color=p.text_secondary, transform=ax.transAxes)

        self.tag_figure.tight_layout()
        self.tag_canvas.draw()
