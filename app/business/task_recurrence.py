from __future__ import annotations

import calendar
import datetime as dt


def compute_next_due_date(current_due_date, recurrence_type, interval=1):
    if recurrence_type == "daily":
        return current_due_date + dt.timedelta(days=interval)

    if recurrence_type == "weekly":
        return current_due_date + dt.timedelta(weeks=interval)

    if recurrence_type == "monthly":
        month = current_due_date.month - 1 + interval
        year = current_due_date.year + month // 12
        month = month % 12 + 1
        last_day = calendar.monthrange(year, month)[1]
        day = min(current_due_date.day, last_day)
        return dt.date(year, month, day)

    return current_due_date
