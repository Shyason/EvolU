from __future__ import annotations

import datetime as dt

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from app.business.scheduling import is_habit_due_on

DAY_LETTERS = ["M", "T", "W", "T", "F", "S", "S"]


def build_weekly_dots(habit, completed_dates, today):
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)

    monday = today - dt.timedelta(days=today.weekday())

    for i in range(7):
        day = monday + dt.timedelta(days=i)
        dot = QLabel(DAY_LETTERS[i])
        dot.setFixedSize(18, 18)
        dot.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if day > today:
            style = "color: #64748B; background: transparent; font-size: 9px;"
        elif not is_habit_due_on(habit, day):
            style = "color: #64748B; background: #1F2C45; border-radius: 9px; font-size: 9px;"
        elif day in completed_dates:
            style = "color: #0F172A; background: #22C55E; border-radius: 9px; font-weight: 700; font-size: 9px;"
        else:
            style = "color: #FB7185; background: transparent; border: 1.5px solid #FB7185; border-radius: 9px; font-size: 9px;"

        dot.setStyleSheet(style)
        layout.addWidget(dot)

    return container
