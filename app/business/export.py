from __future__ import annotations

import csv
import datetime as dt
import json
from pathlib import Path

from app.data.models import Habit, HabitCompletion, Profile, Tag, Task


def _serialize_value(value):
    """JSON can't natively handle date/time objects — convert them to strings."""
    if isinstance(value, (dt.date, dt.datetime, dt.time)):
        return value.isoformat()
    return value


def build_export_data(
    profile: Profile,
    tags: list[Tag],
    tasks: list[Task],
    habits: list[Habit],
    completions_by_habit: dict[int, list[HabitCompletion]],
) -> dict:
    """Assemble everything for one profile into a single nested, JSON-ready dict."""
    return {
        "exported_at": dt.datetime.now().isoformat(),
        "profile": {"id": profile.id, "name": profile.name},
        "tags": [
            {"id": t.id, "name": t.name, "color_hex": t.color_hex} for t in tags
        ],
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "notes": t.notes,
                "due_date": _serialize_value(t.due_date),
                "due_time": _serialize_value(t.due_time),
                "priority": t.priority,
                "tag_id": t.tag_id,
                "habit_id": t.habit_id,
                "is_completed": t.is_completed,
                "completed_at": _serialize_value(t.completed_at),
            }
            for t in tasks
        ],
        "habits": [
            {
                "id": h.id,
                "title": h.title,
                "notes": h.notes,
                "tag_id": h.tag_id,
                "recurrence_type": h.recurrence_type,
                "recurrence_params": h.recurrence_params,
                "streak_rule_type": h.streak_rule_type,
                "streak_rule_params": h.streak_rule_params,
                "current_streak": h.current_streak,
                "longest_streak": h.longest_streak,
                "completions": [
                    _serialize_value(c.date) for c in completions_by_habit.get(h.id, [])
                ],
            }
            for h in habits
        ],
    }


def write_json_export(data: dict, path: Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def write_csv_export(data: dict, directory: Path) -> tuple[Path, Path]:
    """Writes tasks.csv and habits.csv into `directory`. Returns both paths."""
    tag_names_by_id = {t["id"]: t["name"] for t in data["tags"]}

    tasks_path = directory / "tasks.csv"
    with open(tasks_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Title", "Due Date", "Due Time", "Priority", "Tag", "Completed", "Notes"])
        for t in data["tasks"]:
            writer.writerow([
                t["title"],
                t["due_date"] or "",
                t["due_time"] or "",
                t["priority"],
                tag_names_by_id.get(t["tag_id"], ""),
                "Yes" if t["is_completed"] else "No",
                t["notes"] or "",
            ])

    habits_path = directory / "habits.csv"
    with open(habits_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Title", "Recurrence", "Tag", "Current Streak", "Longest Streak", "Total Completions"])
        for h in data["habits"]:
            writer.writerow([
                h["title"],
                h["recurrence_type"],
                tag_names_by_id.get(h["tag_id"], ""),
                h["current_streak"],
                h["longest_streak"],
                len(h["completions"]),
            ])

    return tasks_path, habits_path