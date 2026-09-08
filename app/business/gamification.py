from __future__ import annotations

from dataclasses import dataclass


def xp_required_for_level(level: int) -> int:
    """XP needed to go from `level` to `level + 1`."""
    return 100 * level


@dataclass
class LevelProgress:
    level: int
    xp_into_level: int
    xp_needed_for_level: int
    progress_fraction: float  # 0.0 to 1.0, for a progress bar


def get_level_progress(total_xp: int) -> LevelProgress:
    """Given a profile's total accumulated XP, figure out their current
    level and how far into it they are."""
    level = 1
    remaining_xp = total_xp

    while remaining_xp >= xp_required_for_level(level):
        remaining_xp -= xp_required_for_level(level)
        level += 1

    needed = xp_required_for_level(level)
    return LevelProgress(
        level=level,
        xp_into_level=remaining_xp,
        xp_needed_for_level=needed,
        progress_fraction=remaining_xp / needed,
    )