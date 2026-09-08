from __future__ import annotations

import datetime as dt

from app.data.models import Habit


def is_habit_due_on(habit: Habit, date: dt.date) -> bool:
    """Given a habit's recurrence rule, decide whether it's scheduled for `date`."""
    recurrence_type = habit.recurrence_type
    params = habit.recurrence_params or {}

    if recurrence_type == "daily":
        return True

    if recurrence_type == "weekdays":
        # params example: {"days": ["mon", "wed", "fri"]}
        weekday_names = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        scheduled_days = params.get("days", [])
        return weekday_names[date.weekday()] in scheduled_days

    if recurrence_type == "custom_interval":
        # params example: {"interval_days": 3} — every 3rd day, counting from habit creation
        interval_days = params.get("interval_days", 1)
        anchor_date = habit.created_at.date()
        days_since_anchor = (date - anchor_date).days
        return days_since_anchor >= 0 and days_since_anchor % interval_days == 0

    return False

def describe_recurrence(recurrence_type: str, recurrence_params: dict) -> str:
    if recurrence_type == "daily":
        return "Every day"
    if recurrence_type == "weekdays":
        label_map = {"mon": "Mon", "tue": "Tue", "wed": "Wed", "thu": "Thu",
                     "fri": "Fri", "sat": "Sat", "sun": "Sun"}
        days = recurrence_params.get("days", [])
        return ", ".join(label_map.get(d, d) for d in days) if days else "Weekdays"
    if recurrence_type == "custom_interval":
        return f"Every {recurrence_params.get('interval_days', '?')} days"
    return recurrence_type