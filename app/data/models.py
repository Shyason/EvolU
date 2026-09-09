from __future__ import annotations

import datetime as dt

from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.data.database import Base


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    is_dark_mode: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[dt.datetime] = mapped_column(default=dt.datetime.utcnow)
    xp: Mapped[int] = mapped_column(default=0)
    level: Mapped[int] = mapped_column(default=1)

    tags: Mapped[list["Tag"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    tasks: Mapped[list["Task"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    habits: Mapped[list["Habit"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    unlocked_achievements: Mapped[list["UnlockedAchievement"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id"))
    name: Mapped[str] = mapped_column(String(50))
    color_hex: Mapped[str] = mapped_column(String(7), default="#888888")

    profile: Mapped["Profile"] = relationship(back_populates="tags")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id"))
    tag_id: Mapped[int | None] = mapped_column(ForeignKey("tags.id"), nullable=True)
    habit_id: Mapped[int | None] = mapped_column(ForeignKey("habits.id"), nullable=True)

    title: Mapped[str] = mapped_column(String(200))
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    due_date: Mapped[dt.date | None] = mapped_column(nullable=True)
    due_time: Mapped[dt.time | None] = mapped_column(nullable=True)
    priority: Mapped[str] = mapped_column(String(10), default="medium")  # "low" / "medium" / "high"

    is_completed: Mapped[bool] = mapped_column(default=False)
    completed_at: Mapped[dt.datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(default=dt.datetime.utcnow)

    reminder_minutes_before: Mapped[int | None] = mapped_column(nullable=True)

    profile: Mapped["Profile"] = relationship(back_populates="tasks")
    tag: Mapped[Tag | None] = relationship()
    habit: Mapped[Habit | None] = relationship(back_populates="generated_tasks")

    is_recurring: Mapped[bool] = mapped_column(default=False)
    recurrence_type: Mapped[str | None] = mapped_column(String(20), nullable=True)  # "daily" / "weekly" / "monthly"
    recurrence_interval: Mapped[int] = mapped_column(default=1)


class Habit(Base):
    __tablename__ = "habits"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id"))
    tag_id: Mapped[int | None] = mapped_column(ForeignKey("tags.id"), nullable=True)

    title: Mapped[str] = mapped_column(String(200))
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    # "daily" / "weekdays" / "custom_interval"
    recurrence_type: Mapped[str] = mapped_column(String(20))
    # e.g. {"days": ["mon","wed","fri"]} or {"interval_days": 3}
    recurrence_params: Mapped[dict] = mapped_column(JSON, default=dict)

    # "strict" / "grace_days" / "tolerance_window"
    streak_rule_type: Mapped[str] = mapped_column(String(20), default="strict")
    # e.g. {"grace_tokens_per_month": 2} or {"max_misses": 1, "window_days": 7}
    streak_rule_params: Mapped[dict] = mapped_column(JSON, default=dict)

    current_streak: Mapped[int] = mapped_column(default=0)
    longest_streak: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[dt.datetime] = mapped_column(default=dt.datetime.utcnow)

    reminder_minutes_before: Mapped[int | None] = mapped_column(nullable=True)

    profile: Mapped["Profile"] = relationship(back_populates="habits")
    tag: Mapped["Tag | None"] = relationship()
    completions: Mapped[list["HabitCompletion"]] = relationship(
        back_populates="habit", cascade="all, delete-orphan"
    )
    generated_tasks: Mapped[list["Task"]] = relationship(back_populates="habit")


class HabitCompletion(Base):
    __tablename__ = "habit_completions"

    id: Mapped[int] = mapped_column(primary_key=True)
    habit_id: Mapped[int] = mapped_column(ForeignKey("habits.id"))
    date: Mapped[dt.date] = mapped_column()
    completed_at: Mapped[dt.datetime] = mapped_column(default=dt.datetime.utcnow)

    habit: Mapped["Habit"] = relationship(back_populates="completions")


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id"))
    item_type: Mapped[str] = mapped_column(String(10))  # "task" or "habit"
    item_id: Mapped[int] = mapped_column()
    message: Mapped[str] = mapped_column(String(300))
    triggered_at: Mapped[dt.datetime] = mapped_column(default=dt.datetime.utcnow)
    was_seen: Mapped[bool] = mapped_column(default=False)

class Achievement(Base):
    """Static catalog of every achievement that exists in the app. Not
    tied to a profile — this table is the same for everyone. Seeded once
    at startup (see seed_achievements() below)."""
    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)  # stable key, e.g. "streak_7"
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(300))
    icon: Mapped[str] = mapped_column(String(10), default="🏆")  # emoji, used until Step 6's icon pass


class UnlockedAchievement(Base):
    __tablename__ = "unlocked_achievements"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id"))
    achievement_id: Mapped[int] = mapped_column(ForeignKey("achievements.id"))
    unlocked_at: Mapped[dt.datetime] = mapped_column(default=dt.datetime.utcnow)

    profile: Mapped["Profile"] = relationship(back_populates="unlocked_achievements")
    achievement: Mapped["Achievement"] = relationship()

class FocusSession(Base):
    __tablename__ = "focus_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id"))
    started_at: Mapped[dt.datetime] = mapped_column(default=dt.datetime.utcnow)
    ended_at: Mapped[dt.datetime | None] = mapped_column(nullable=True)
    duration_seconds: Mapped[int] = mapped_column(default=0)
