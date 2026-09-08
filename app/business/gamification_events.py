from __future__ import annotations

from dataclasses import dataclass, field

XP_PER_TASK = 10
XP_PER_HABIT = 15


@dataclass
class GamificationResult:
    xp_awarded: int
    leveled_up: bool
    new_level: int | None = None
    newly_unlocked: list[str] = field(default_factory=list)  # achievement codes


def check_achievement_unlocks(
    unlocked_codes: set[str],
    total_tasks_completed: int,
    max_current_streak: int,
    current_level: int,
) -> list[str]:
    """Pure function: given current stats, return achievement codes that
    should now be unlocked but aren't yet. No database access here —
    the caller handles persisting the unlock."""
    newly_unlocked = []

    def maybe_unlock(code: str, condition: bool):
        if condition and code not in unlocked_codes:
            newly_unlocked.append(code)

    maybe_unlock("first_task", total_tasks_completed >= 1)
    maybe_unlock("tasks_10", total_tasks_completed >= 10)
    maybe_unlock("tasks_50", total_tasks_completed >= 50)
    maybe_unlock("streak_3", max_current_streak >= 3)
    maybe_unlock("streak_7", max_current_streak >= 7)
    maybe_unlock("streak_30", max_current_streak >= 30)
    maybe_unlock("level_5", current_level >= 5)
    maybe_unlock("level_10", current_level >= 10)

    return newly_unlocked