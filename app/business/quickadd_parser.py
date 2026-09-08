from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass

from dateparser.search import search_dates

TIME_PATTERN = re.compile(r"\d{1,2}(:\d{2})?\s*(am|pm)\b|\b\d{1,2}:\d{2}\b", re.IGNORECASE)


@dataclass
class QuickAddResult:
    title: str
    due_date: dt.date | None
    due_time: dt.time | None
    matched_text: str | None  # the substring dateparser recognized, for UI preview purposes


def parse_quick_add(text: str, now: dt.datetime | None = None) -> QuickAddResult:
    """Parse a quick-add string like 'gym tomorrow 6pm' into a title + optional due date/time."""
    now = now or dt.datetime.now()
    text = text.strip()

    if not text:
        return QuickAddResult(title="", due_date=None, due_time=None, matched_text=None)

    results = search_dates(
        text,
        languages=["en"],
        settings={"PREFER_DATES_FROM": "future", "RELATIVE_BASE": now},
    )

    if not results:
        return QuickAddResult(title=text, due_date=None, due_time=None, matched_text=None)

    # If multiple date-like phrases were found, the last one is usually the
    # intended due date (titles more often start with the task, not the date).
    matched_text, parsed_dt = results[-1]

    title = text.replace(matched_text, "").strip()
    title = re.sub(r"\s+", " ", title).strip(" ,-")

    if not title:
        # Guard: if stripping the date left nothing (e.g. someone typed just "tomorrow"),
        # fall back to the original text rather than saving a blank title.
        title = text

    has_explicit_time = bool(TIME_PATTERN.search(matched_text))

    return QuickAddResult(
        title=title,
        due_date=parsed_dt.date(),
        due_time=parsed_dt.time() if has_explicit_time else None,
        matched_text=matched_text,
    )

@dataclass
class HabitQuickAddResult:
    title: str
    recurrence_type: str
    recurrence_params: dict
    matched_text: str | None


_INTERVAL_PATTERN = re.compile(r"\bevery\s+(\d+)\s+days?\b", re.IGNORECASE)
_DAILY_PATTERN = re.compile(r"\b(daily|every day)\b", re.IGNORECASE)
_WEEKDAYS_PATTERN = re.compile(r"\bweekdays\b", re.IGNORECASE)


def parse_habit_quick_add(text: str) -> HabitQuickAddResult:
    text = text.strip()
    if not text:
        return HabitQuickAddResult(title="", recurrence_type="daily", recurrence_params={}, matched_text=None)

    if match := _INTERVAL_PATTERN.search(text):
        return HabitQuickAddResult(
            title=_strip_match(text, match.group(0)),
            recurrence_type="custom_interval",
            recurrence_params={"interval_days": int(match.group(1))},
            matched_text=match.group(0),
        )

    if match := _WEEKDAYS_PATTERN.search(text):
        return HabitQuickAddResult(
            title=_strip_match(text, match.group(0)),
            recurrence_type="weekdays",
            recurrence_params={"days": ["mon", "tue", "wed", "thu", "fri"]},
            matched_text=match.group(0),
        )

    if match := _DAILY_PATTERN.search(text):
        return HabitQuickAddResult(
            title=_strip_match(text, match.group(0)),
            recurrence_type="daily",
            recurrence_params={},
            matched_text=match.group(0),
        )

    # No recognized recurrence phrase — default to daily, keep the full text as title.
    return HabitQuickAddResult(title=text, recurrence_type="daily", recurrence_params={}, matched_text=None)


def _strip_match(text: str, matched: str) -> str:
    title = text.replace(matched, "")
    title = re.sub(r"\s+", " ", title).strip(" ,-")
    return title or text