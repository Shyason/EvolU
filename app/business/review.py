from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from app.business.scheduling import is_habit_due_on
from app.data.models import Habit, Task


@dataclass
class DailyReview:
    date: dt.date
    tasks_completed: int
    tasks_total: int
    habits_completed: int
    habits_due: int
    overdue_task_titles: list[str]
    habit_streaks: list[tuple[str, int]]  # (title, current_streak)


@dataclass
class WeeklyReview:
    start_date: dt.date
    end_date: dt.date
    tasks_completed: int
    tasks_total: int
    habit_completion_rate: float | None  # None if nothing was ever due
    best_habit: tuple[str, int] | None  # (title, current_streak)
    worst_habit: tuple[str, int] | None
    missed_habit_days: int


def build_daily_review(
    tasks: list[Task], habits: list[Habit], completions_by_habit: dict[int, set[dt.date]], date: dt.date
) -> DailyReview:
    tasks_today = [t for t in tasks if t.due_date == date]
    habits_due_today = [h for h in habits if is_habit_due_on(h, date)]

    overdue = [
        t.title for t in tasks
        if t.due_date and t.due_date < date and not t.is_completed
    ]

    return DailyReview(
        date=date,
        tasks_completed=sum(1 for t in tasks_today if t.is_completed),
        tasks_total=len(tasks_today),
        habits_completed=sum(
            1 for h in habits_due_today if date in completions_by_habit.get(h.id, set())
        ),
        habits_due=len(habits_due_today),
        overdue_task_titles=overdue,
        habit_streaks=[(h.title, h.current_streak) for h in habits],
    )


def build_weekly_review(
    tasks: list[Task], habits: list[Habit], completions_by_habit: dict[int, set[dt.date]], end_date: dt.date
) -> WeeklyReview:
    start_date = end_date - dt.timedelta(days=6)

    tasks_in_range = [t for t in tasks if t.due_date and start_date <= t.due_date <= end_date]

    due_count = 0
    completed_count = 0
    day = start_date
    while day <= end_date:
        for habit in habits:
            if is_habit_due_on(habit, day):
                due_count += 1
                if day in completions_by_habit.get(habit.id, set()):
                    completed_count += 1
        day += dt.timedelta(days=1)

    completion_rate = completed_count / due_count if due_count > 0 else None
    missed = due_count - completed_count

    habits_with_streaks = [(h.title, h.current_streak) for h in habits]
    best = max(habits_with_streaks, key=lambda pair: pair[1]) if habits_with_streaks else None
    worst = min(habits_with_streaks, key=lambda pair: pair[1]) if habits_with_streaks else None

    return WeeklyReview(
        start_date=start_date,
        end_date=end_date,
        tasks_completed=sum(1 for t in tasks_in_range if t.is_completed),
        tasks_total=len(tasks_in_range),
        habit_completion_rate=completion_rate,
        best_habit=best,
        worst_habit=worst,
        missed_habit_days=missed,
    )