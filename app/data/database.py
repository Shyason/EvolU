from pathlib import Path

from platformdirs import user_data_dir
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

APP_NAME = "TodoHabitApp"
APP_AUTHOR = "YourName"  # used only on Windows to build the folder path


def get_data_dir() -> Path:
    """Return the OS-appropriate folder for this app's data, creating it if needed."""
    data_dir = Path(user_data_dir(APP_NAME, APP_AUTHOR))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_database_path() -> Path:
    return get_data_dir() / "app_data.db"


class Base(DeclarativeBase):
    """Base class every ORM model inherits from. SQLAlchemy uses this
    to keep track of all the tables we define."""
    pass


engine = create_engine(f"sqlite:///{get_database_path()}", echo=False)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    """Create all tables that don't already exist. Safe to call every app startup."""
    from app.data import models
    Base.metadata.create_all(bind=engine)
    seed_achievements()

def seed_achievements() -> None:
    """Insert the achievement catalog if it doesn't already exist. Safe to
    call on every app startup — skips any achievement whose code already exists."""
    from app.data.models import Achievement

    catalog = [
        ("first_task", "Getting Started", "Complete your first task", "🌱"),
        ("first_habit", "Habit Former", "Create your first habit", "🌿"),
        ("streak_3", "On a Roll", "Reach a 3-day streak on any habit", "🔥"),
        ("streak_7", "Week Warrior", "Reach a 7-day streak on any habit", "🔥"),
        ("streak_30", "Unstoppable", "Reach a 30-day streak on any habit", "🏆"),
        ("tasks_10", "Task Crusher", "Complete 10 tasks total", "⚡"),
        ("tasks_50", "Productivity Machine", "Complete 50 tasks total", "⚡"),
        ("level_5", "Rising Star", "Reach level 5", "⭐"),
        ("level_10", "Veteran", "Reach level 10", "⭐"),
    ]

    with SessionLocal() as session:
        existing_codes = {a.code for a in session.query(Achievement).all()}
        for code, title, description, icon in catalog:
            if code not in existing_codes:
                session.add(Achievement(code=code, title=title, description=description, icon=icon))
        session.commit()