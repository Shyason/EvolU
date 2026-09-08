from __future__ import annotations

from app.business.gamification import get_level_progress
from app.business.gamification_events import (
    XP_PER_HABIT,
    XP_PER_TASK,
    GamificationResult,
    check_achievement_unlocks,
)
from app.data.achievement_repository import AchievementRepository
from app.data.repository import HabitRepository, ProfileRepository, TaskRepository


class GamificationService:
    def __init__(self):
        self.profile_repo = ProfileRepository()
        self.task_repo = TaskRepository()
        self.habit_repo = HabitRepository()
        self.achievement_repo = AchievementRepository()

    def award_for_task_completion(self, profile_id: int) -> GamificationResult:
        return self._award(profile_id, XP_PER_TASK)

    def award_for_habit_completion(self, profile_id: int) -> GamificationResult:
        return self._award(profile_id, XP_PER_HABIT)

    def revert_for_uncomplete(self, profile_id: int, xp_amount: int) -> None:
        """Called when a task/habit gets un-checked — removes the XP that
        was granted, without re-checking achievements (achievements, once
        earned, stay earned even if you later undo the action)."""
        self.profile_repo.add_xp(profile_id, -xp_amount)

    def _award(self, profile_id: int, xp_amount: int) -> GamificationResult:
        profile_before = self.profile_repo.get_by_id(profile_id)
        level_before = get_level_progress(profile_before.xp).level

        updated_profile = self.profile_repo.add_xp(profile_id, xp_amount)
        progress_after = get_level_progress(updated_profile.xp)

        leveled_up = progress_after.level > level_before
        if leveled_up:
            self.profile_repo.set_level(profile_id, progress_after.level)

        newly_unlocked = self._check_and_unlock_achievements(profile_id, progress_after.level)

        return GamificationResult(
            xp_awarded=xp_amount,
            leveled_up=leveled_up,
            new_level=progress_after.level if leveled_up else None,
            newly_unlocked=newly_unlocked,
        )

    def _check_and_unlock_achievements(self, profile_id: int, current_level: int) -> list[str]:
        tasks = self.task_repo.get_all(profile_id)
        habits = self.habit_repo.get_all(profile_id)
        unlocked_codes = self.achievement_repo.get_unlocked_codes(profile_id)

        total_completed = sum(1 for t in tasks if t.is_completed)
        max_streak = max((h.current_streak for h in habits), default=0)

        codes_to_unlock = check_achievement_unlocks(unlocked_codes, total_completed, max_streak, current_level)
        for code in codes_to_unlock:
            self.achievement_repo.unlock(profile_id, code)

        return codes_to_unlock