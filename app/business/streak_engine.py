from __future__ import annotations

import datetime as dt

from app.business.scheduling import is_habit_due_on
from app.data.models import Habit


def calculate_current_streak(
    habit: Habit, completed_dates: set[dt.date], as_of_date: dt.date
) -> int:
    """Dispatches to the correct rule based on habit.streak_rule_type."""
    rule_type = habit.streak_rule_type
    params = habit.streak_rule_params or {}

    if rule_type == "grace_days":
        return _streak_with_grace_days(habit, completed_dates, as_of_date, params)
    if rule_type == "tolerance_window":
        return _streak_with_tolerance_window(habit, completed_dates, as_of_date, params)
    # default / "strict"
    return _streak_strict(habit, completed_dates, as_of_date)


def calculate_longest_streak(habit: Habit, completed_dates: set[dt.date]) -> int:
    """Scans a habit's entire history to find its best-ever run.
    Uses the same rule as current streak, just replayed across every date
    that was ever scheduled, rather than counting backward from today."""
    if not completed_dates:
        return 0

    earliest = min(completed_dates)
    latest = max(completed_dates)
    longest = 0
    day = earliest
    while day <= latest:
        streak_ending_here = calculate_current_streak(habit, completed_dates, day)
        longest = max(longest, streak_ending_here)
        day += dt.timedelta(days=1)
    return longest


# --- Individual rule implementations ---

def _streak_strict(habit: Habit, completed_dates: set[dt.date], as_of_date: dt.date) -> int:
    """Miss one scheduled day -> streak breaks. Today counts as 'not yet broken'
    if it's simply not done yet (you still have time left in the day)."""
    streak = 0
    date = as_of_date
    while True:
        if not is_habit_due_on(habit, date):
            date -= dt.timedelta(days=1)
            continue
        if date in completed_dates:
            streak += 1
            date -= dt.timedelta(days=1)
        elif date == as_of_date:
            # Today's due but not done yet — don't count it, don't break either.
            date -= dt.timedelta(days=1)
            continue
        else:
            break
    return streak


def _streak_with_grace_days(
    habit: Habit, completed_dates: set[dt.date], as_of_date: dt.date, params: dict
) -> int:
    """Like strict, but a limited number of missed scheduled days don't break
    the streak — they just consume a 'grace token' instead.

    Simplification for v1: grace_tokens_per_month is treated as a flat total
    budget of misses tolerated across the whole lookback, not a rolling
    monthly allowance that replenishes. That's simpler to reason about and
    covers the common case; a true rolling allowance is a reasonable v2
    enhancement if you find you want it."""
    grace_budget = params.get("grace_tokens_per_month", 0)
    streak = 0
    grace_used = 0
    date = as_of_date
    while True:
        if not is_habit_due_on(habit, date):
            date -= dt.timedelta(days=1)
            continue
        if date in completed_dates:
            streak += 1
            date -= dt.timedelta(days=1)
        elif date == as_of_date:
            date -= dt.timedelta(days=1)
            continue
        elif grace_used < grace_budget:
            grace_used += 1
            date -= dt.timedelta(days=1)  # miss forgiven, streak continues, doesn't increment
        else:
            break
    return streak


def _streak_with_tolerance_window(
    habit: Habit, completed_dates: set[dt.date], as_of_date: dt.date, params: dict
) -> int:
    """The streak holds as long as, within any trailing window of
    `window_days` scheduled days, you've missed no more than `max_misses`."""
    window_days = params.get("window_days", 7)
    max_misses = params.get("max_misses", 1)

    # Walk backward collecting scheduled days until we've gathered `window_days` of them.
    scheduled_dates: list[dt.date] = []
    date = as_of_date
    while len(scheduled_dates) < window_days:
        if is_habit_due_on(habit, date):
            scheduled_dates.append(date)
        date -= dt.timedelta(days=1)
        if date < as_of_date - dt.timedelta(days=365):
            break  # safety valve for habits with very sparse schedules

    misses_in_window = sum(
        1 for d in scheduled_dates if d != as_of_date and d not in completed_dates
    )
    if misses_in_window > max_misses:
        return 0

    # If the window holds, streak length = consecutive scheduled days counted
    # the same way as strict (tolerance affects *whether* it's broken, not the count).
    return _streak_strict(habit, completed_dates, as_of_date)