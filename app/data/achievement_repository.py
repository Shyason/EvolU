from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.data.database import SessionLocal
from app.data.models import Achievement, UnlockedAchievement


class AchievementRepository:
    def get_all(self) -> list[Achievement]:
        with SessionLocal() as session:
            return list(session.scalars(select(Achievement)).all())

    def get_unlocked_codes(self, profile_id: int) -> set[str]:
        with SessionLocal() as session:
            stmt = (
                select(UnlockedAchievement)
                .where(UnlockedAchievement.profile_id == profile_id)
                .options(selectinload(UnlockedAchievement.achievement))
            )
            return {ua.achievement.code for ua in session.scalars(stmt).all()}

    def unlock(self, profile_id: int, achievement_code: str) -> UnlockedAchievement | None:
        with SessionLocal() as session:
            achievement = session.scalar(
                select(Achievement).where(Achievement.code == achievement_code)
            )
            if achievement is None:
                return None
            unlocked = UnlockedAchievement(profile_id=profile_id, achievement_id=achievement.id)
            session.add(unlocked)
            session.commit()
            session.refresh(unlocked)
            return unlocked

    def get_unlocked_with_details(self, profile_id: int) -> list[UnlockedAchievement]:
        with SessionLocal() as session:
            stmt = (
                select(UnlockedAchievement)
                .where(UnlockedAchievement.profile_id == profile_id)
                .options(selectinload(UnlockedAchievement.achievement))
            )
            return list(session.scalars(stmt).all())