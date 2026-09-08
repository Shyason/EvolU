from __future__ import annotations

import datetime as dt

from plyer import notification as os_notification

from app.business.notifications import get_due_task_reminders
from app.data.models import Task
from app.data.repository import NotificationLogRepository, TaskRepository


class NotificationService:
    def __init__(self):
        self.task_repo = TaskRepository()
        self.log_repo = NotificationLogRepository()

    def check_and_fire(self, profile_id: int) -> None:
        now = dt.datetime.now()
        tasks = self.task_repo.get_all(profile_id)
        due_tasks = get_due_task_reminders(tasks, now)

        already_notified_ids = {
            log.item_id for log in self.log_repo.get_all(profile_id) if log.item_type == "task"
        }

        for task in due_tasks:
            if task.id not in already_notified_ids:
                self._fire(profile_id, task)

    def _fire(self, profile_id: int, task: Task) -> None:
        message = f"Due at {task.due_time.strftime('%I:%M %p').lstrip('0')}" if task.due_time else "Due today"
        try:
            os_notification.notify(title=task.title, message=message, timeout=10, app_icon="app/ui/icons/app_icon.ico")
        except Exception:
            pass  # a failed native/OS notification shouldn't crash the app
        self.log_repo.add(profile_id, "task", task.id, f"{task.title} — {message}")