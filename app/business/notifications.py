from __future__ import annotations

import datetime as dt

from app.data.models import NotificationLog, Task


def get_due_task_reminders(tasks: list[Task], now: dt.datetime) -> list[Task]:
    """Return tasks whose reminder window has opened: due datetime minus
    reminder_minutes_before has passed, but the due moment itself hasn't
    passed by more than a day (avoids re-surfacing very stale reminders
    after the app's been closed a while)."""
    due = []
    for task in tasks:
        if task.is_completed or task.due_date is None or task.reminder_minutes_before is None:
            continue

        due_time = task.due_time or dt.time(0, 0)
        due_datetime = dt.datetime.combine(task.due_date, due_time)
        remind_at = due_datetime - dt.timedelta(minutes=task.reminder_minutes_before)

        if remind_at <= now <= due_datetime + dt.timedelta(days=1):
            due.append(task)
    return due