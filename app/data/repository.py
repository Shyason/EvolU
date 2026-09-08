from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.data.database import SessionLocal
from app.data.models import (
    Habit,
    HabitCompletion,
    NotificationLog,
    Profile,
    Tag,
    Task,
)


class ProfileRepository:
    def create(self, name: str) -> Profile:
        with SessionLocal() as session:
            profile = Profile(name=name)
            session.add(profile)
            session.commit()
            session.refresh(profile)
            return profile

    def get_all(self) -> list[Profile]:
        with SessionLocal() as session:
            return list(session.scalars(select(Profile)).all())

    def get_by_id(self, profile_id: int) -> Profile | None:
        with SessionLocal() as session:
            return session.get(Profile, profile_id)

    def set_dark_mode(self, profile_id: int, is_dark_mode: bool) -> None:
        with SessionLocal() as session:
            profile = session.get(Profile, profile_id)
            if profile:
                profile.is_dark_mode = is_dark_mode
                session.commit()

    def add_xp(self, profile_id: int, amount: int) -> Profile | None:
        with SessionLocal() as session:
            profile = session.get(Profile, profile_id)
            if profile is None:
                return None
            profile.xp += amount
            session.commit()
            session.refresh(profile)
            return profile

    def set_level(self, profile_id: int, level: int) -> None:
        with SessionLocal() as session:
            profile = session.get(Profile, profile_id)
            if profile:
                profile.level = level
                session.commit()

    def rename(self, profile_id, new_name):
        with SessionLocal() as session:
            profile = session.get(Profile, profile_id)
            if profile is None:
                return None
            profile.name = new_name
            session.commit()
            session.refresh(profile)
            return profile

    def delete(self, profile_id):
        with SessionLocal() as session:
            profile = session.get(Profile, profile_id)
            if profile is None:
                return False
            session.delete(profile)
            session.commit()
            return True

class TagRepository:
    def create(self, profile_id: int, name: str, color_hex: str = "#888888") -> Tag:
        with SessionLocal() as session:
            tag = Tag(profile_id=profile_id, name=name, color_hex=color_hex)
            session.add(tag)
            session.commit()
            session.refresh(tag)
            return tag

    def get_for_profile(self, profile_id: int) -> list[Tag]:
        with SessionLocal() as session:
            stmt = select(Tag).where(Tag.profile_id == profile_id)
            return list(session.scalars(stmt).all())

    def update(self, tag_id, **fields):
        with SessionLocal() as session:
            tag = session.get(Tag, tag_id)
            if tag is None:
                return None
            for key, value in fields.items():
                setattr(tag, key, value)
            session.commit()
            session.refresh(tag)
            return tag

    def delete(self, tag_id):
        with SessionLocal() as session:
            tag = session.get(Tag, tag_id)
            if tag is None:
                return False
            session.delete(tag)
            session.commit()
            return True

class TaskRepository:
    def create(
        self,
        profile_id: int,
        title: str,
        due_date: dt.date | None = None,
        due_time: dt.time | None = None,
        priority: str = "medium",
        tag_id: int | None = None,
        habit_id: int | None = None,
        notes: str | None = None,
        reminder_minutes_before: int | None = None,
    ) -> Task:
        with SessionLocal() as session:
            task = Task(
                profile_id=profile_id,
                title=title,
                due_date=due_date,
                due_time=due_time,
                priority=priority,
                tag_id=tag_id,
                habit_id=habit_id,
                notes=notes,
                reminder_minutes_before=reminder_minutes_before,
            )
            session.add(task)
            session.commit()
            session.refresh(task)
            return task

    def get_today(self, profile_id: int, today: dt.date | None = None) -> list[Task]:
        today = today or dt.date.today()
        with SessionLocal() as session:
            stmt = (
                select(Task)
                .where(Task.profile_id == profile_id, Task.due_date == today)
                .options(selectinload(Task.tag))
            )
            return list(session.scalars(stmt).all())

    def get_all(self, profile_id: int) -> list[Task]:
        with SessionLocal() as session:
            stmt = (
                select(Task)
                .where(Task.profile_id == profile_id)
                .options(selectinload(Task.tag))
            )
            return list(session.scalars(stmt).all())

    def get_by_id(self, task_id: int) -> Task | None:
        with SessionLocal() as session:
            return session.get(Task, task_id)

    def toggle_complete(self, task_id: int) -> Task | None:
        with SessionLocal() as session:
            task = session.get(Task, task_id)
            if task is None:
                return None
            task.is_completed = not task.is_completed
            task.completed_at = dt.datetime.utcnow() if task.is_completed else None
            session.commit()
            session.refresh(task)
            return task

    def update(self, task_id: int, **fields) -> Task | None:
        with SessionLocal() as session:
            task = session.get(Task, task_id)
            if task is None:
                return None
            for key, value in fields.items():
                setattr(task, key, value)
            session.commit()
            session.refresh(task)
            return task

    def delete(self, task_id: int) -> bool:
        with SessionLocal() as session:
            task = session.get(Task, task_id)
            if task is None:
                return False
            session.delete(task)
            session.commit()
            return True


class HabitRepository:
    def create(
        self,
        profile_id: int,
        title: str,
        recurrence_type: str,
        recurrence_params: dict,
        streak_rule_type: str = "strict",
        streak_rule_params: dict | None = None,
        tag_id: int | None = None,
        notes: str | None = None,
        reminder_minutes_before: int | None = None,
    ) -> Habit:
        with SessionLocal() as session:
            habit = Habit(
                profile_id=profile_id,
                title=title,
                recurrence_type=recurrence_type,
                recurrence_params=recurrence_params,
                streak_rule_type=streak_rule_type,
                streak_rule_params=streak_rule_params or {},
                tag_id=tag_id,
                notes=notes,
                reminder_minutes_before=reminder_minutes_before,
            )
            session.add(habit)
            session.commit()
            session.refresh(habit)
            return habit

    def get_all(self, profile_id: int) -> list[Habit]:
        with SessionLocal() as session:
            stmt = (
                select(Habit)
                .where(Habit.profile_id == profile_id)
                .options(selectinload(Habit.tag))
            )
            return list(session.scalars(stmt).all())

    def get_by_id(self, habit_id: int) -> Habit | None:
        with SessionLocal() as session:
            stmt = select(Habit).where(Habit.id == habit_id).options(selectinload(Habit.completions))
            return session.scalars(stmt).first()

    def update(self, habit_id: int, **fields) -> Habit | None:
        with SessionLocal() as session:
            habit = session.get(Habit, habit_id)
            if habit is None:
                return None
            for key, value in fields.items():
                setattr(habit, key, value)
            session.commit()
            session.refresh(habit)
            return habit

    def update_streaks(self, habit_id: int, current_streak: int, longest_streak: int) -> None:
        with SessionLocal() as session:
            habit = session.get(Habit, habit_id)
            if habit:
                habit.current_streak = current_streak
                habit.longest_streak = longest_streak
                session.commit()

    def delete(self, habit_id: int) -> bool:
        with SessionLocal() as session:
            habit = session.get(Habit, habit_id)
            if habit is None:
                return False
            session.delete(habit)
            session.commit()
            return True


class HabitCompletionRepository:
    def mark_complete(self, habit_id: int, date: dt.date | None = None) -> HabitCompletion:
        date = date or dt.date.today()
        with SessionLocal() as session:
            completion = HabitCompletion(habit_id=habit_id, date=date)
            session.add(completion)
            session.commit()
            session.refresh(completion)
            return completion

    def get_for_habit(self, habit_id: int) -> list[HabitCompletion]:
        with SessionLocal() as session:
            stmt = select(HabitCompletion).where(HabitCompletion.habit_id == habit_id)
            return list(session.scalars(stmt).all())

    def is_complete_on(self, habit_id: int, date: dt.date) -> bool:
        with SessionLocal() as session:
            stmt = select(HabitCompletion).where(
                HabitCompletion.habit_id == habit_id,
                HabitCompletion.date == date,
            )
            return session.scalars(stmt).first() is not None

    def delete_for_date(self, habit_id: int, date: dt.date) -> bool:
        with SessionLocal() as session:
            stmt = select(HabitCompletion).where(
                HabitCompletion.habit_id == habit_id,
                HabitCompletion.date == date,
            )
            completion = session.scalars(stmt).first()
            if completion is None:
                return False
            session.delete(completion)
            session.commit()
            return True


class NotificationLogRepository:
    def add(self, profile_id: int, item_type: str, item_id: int, message: str) -> NotificationLog:
        with SessionLocal() as session:
            log = NotificationLog(
                profile_id=profile_id,
                item_type=item_type,
                item_id=item_id,
                message=message,
            )
            session.add(log)
            session.commit()
            session.refresh(log)
            return log
    def get_all(self, profile_id: int) -> list[NotificationLog]:
        with SessionLocal() as session:
            stmt = select(NotificationLog).where(NotificationLog.profile_id == profile_id)
            return list(session.scalars(stmt).all())
        
    def get_unseen(self, profile_id: int) -> list[NotificationLog]:
        with SessionLocal() as session:
            stmt = select(NotificationLog).where(
                NotificationLog.profile_id == profile_id,
                NotificationLog.was_seen == False,  # noqa: E712 — SQLAlchemy requires == here, not `is False`
            )
            return list(session.scalars(stmt).all())

    def mark_seen(self, log_id: int) -> None:
        with SessionLocal() as session:
            log = session.get(NotificationLog, log_id)
            if log:
                log.was_seen = True
                session.commit()