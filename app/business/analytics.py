from __future__ import annotations

import datetime as dt
from collections import defaultdict

from app.business.scheduling import is_habit_due_on
from app.data.models import Habit, Task


def calculate_daily_completion_rates(
    habits: list[Habit],
    completions_by_habit: dict[int, set[dt.date]],
    days: int,
    end_date: dt.date,
) -> list[tuple[dt.date, float | None]]:
    """For each of the last `days` days, what fraction of habits due that
    day were actually completed. A day with nothing due returns None
    (not 0%) so the chart can distinguish 'no data' from 'total miss'."""
    results = []
    for offset in range(days - 1, -1, -1):
        day = end_date - dt.timedelta(days=offset)
        due_habits = [h for h in habits if is_habit_due_on(h, day)]
        if not due_habits:
            results.append((day, None))
            continue
        completed = sum(1 for h in due_habits if day in completions_by_habit.get(h.id, set()))
        results.append((day, completed / len(due_habits)))
    return results


def get_streak_comparison(habits: list[Habit]) -> list[tuple[str, int]]:
    """Habit title -> current streak, sorted descending (best first)."""
    pairs = [(h.title, h.current_streak) for h in habits]
    return sorted(pairs, key=lambda pair: pair[1], reverse=True)


def get_completed_tasks_by_tag(tasks: list[Task]) -> dict[str, int]:
    """Tag name -> count of completed tasks under that tag. Untagged
    completed tasks are grouped under 'No tag'."""
    counts: dict[str, int] = defaultdict(int)
    for task in tasks:
        if not task.is_completed:
            continue
        tag_name = task.tag.name if task.tag else "No tag"
        counts[tag_name] += 1
    return dict(counts)