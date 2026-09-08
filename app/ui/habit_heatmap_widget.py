from __future__ import annotations

import datetime as dt

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QToolTip, QWidget

from app.business.scheduling import is_habit_due_on
from app.data.models import Habit

CELL_SIZE = 14
CELL_GAP = 3
WEEKS_TO_SHOW = 26  # roughly 6 months, like GitHub's compact view

COLOR_COMPLETED = QColor("#39d353")
COLOR_MISSED = QColor("#e05252")
COLOR_NOT_SCHEDULED = QColor("#2b2b2b")
COLOR_FUTURE = QColor("#1a1a1a")


class HabitHeatmapWidget(QWidget):
    def __init__(self, habit: Habit, completed_dates: set[dt.date], parent=None):
        super().__init__(parent)
        self.habit = habit
        self.completed_dates = completed_dates
        self.today = dt.date.today()

        # Align the grid start to the Monday of the week, WEEKS_TO_SHOW weeks back.
        days_back = WEEKS_TO_SHOW * 7 - 1
        start = self.today - dt.timedelta(days=days_back)
        self.grid_start = start - dt.timedelta(days=start.weekday())  # snap to that week's Monday

        grid_width = WEEKS_TO_SHOW * (CELL_SIZE + CELL_GAP)
        grid_height = 7 * (CELL_SIZE + CELL_GAP)
        self.setFixedSize(grid_width + 20, grid_height + 20)
        self.setMouseTracking(True)  # lets mouseMoveEvent fire without holding a button down

    def _date_for_cell(self, week: int, weekday: int) -> dt.date:
        return self.grid_start + dt.timedelta(days=week * 7 + weekday)

    def _color_for_date(self, date: dt.date) -> QColor:
        if date > self.today:
            return COLOR_FUTURE
        if date in self.completed_dates:
            return COLOR_COMPLETED
        if is_habit_due_on(self.habit, date):
            return COLOR_MISSED
        return COLOR_NOT_SCHEDULED

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        for week in range(WEEKS_TO_SHOW):
            for weekday in range(7):
                date = self._date_for_cell(week, weekday)
                color = self._color_for_date(date)
                x = 10 + week * (CELL_SIZE + CELL_GAP)
                y = 10 + weekday * (CELL_SIZE + CELL_GAP)
                painter.setBrush(color)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(QRect(x, y, CELL_SIZE, CELL_SIZE), 3, 3)

        painter.end()

    def mouseMoveEvent(self, event) -> None:
        pos = event.position().toPoint()
        week = (pos.x() - 10) // (CELL_SIZE + CELL_GAP)
        weekday = (pos.y() - 10) // (CELL_SIZE + CELL_GAP)

        if 0 <= week < WEEKS_TO_SHOW and 0 <= weekday < 7:
            date = self._date_for_cell(week, weekday)
            if date <= self.today:
                status = (
                    "Completed" if date in self.completed_dates
                    else "Missed" if is_habit_due_on(self.habit, date)
                    else "Not scheduled"
                )
                QToolTip.showText(event.globalPosition().toPoint(), f"{date.strftime('%b %d, %Y')}\n{status}")
                return
        QToolTip.hideText()