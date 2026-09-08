from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QDialog, QFileDialog, QLabel, QMessageBox, QPushButton, QVBoxLayout

from app.business.export import build_export_data, write_csv_export, write_json_export
from app.data.repository import (
    HabitCompletionRepository,
    HabitRepository,
    ProfileRepository,
    TagRepository,
    TaskRepository,
)


class ExportDialog(QDialog):
    def __init__(self, profile_id: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Data")
        self.profile_id = profile_id

        self.profile_repo = ProfileRepository()
        self.tag_repo = TagRepository()
        self.task_repo = TaskRepository()
        self.habit_repo = HabitRepository()
        self.completion_repo = HabitCompletionRepository()

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Export all tasks, habits, and completion history for this profile."))

        json_button = QPushButton("Export as JSON (full backup)")
        json_button.clicked.connect(self._export_json)
        layout.addWidget(json_button)

        csv_button = QPushButton("Export as CSV (tasks.csv + habits.csv)")
        csv_button.clicked.connect(self._export_csv)
        layout.addWidget(csv_button)

    def _gather_data(self) -> dict:
        profile = self.profile_repo.get_by_id(self.profile_id)
        tags = self.tag_repo.get_for_profile(self.profile_id)
        tasks = self.task_repo.get_all(self.profile_id)
        habits = self.habit_repo.get_all(self.profile_id)
        completions_by_habit = {
            habit.id: self.completion_repo.get_for_habit(habit.id) for habit in habits
        }
        return build_export_data(profile, tags, tasks, habits, completions_by_habit)

    def _export_json(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Backup", "todo_habit_backup.json", "JSON Files (*.json)"
        )
        if not file_path:
            return  # user cancelled

        data = self._gather_data()
        write_json_export(data, Path(file_path))
        QMessageBox.information(self, "Export Complete", f"Backup saved to:\n{file_path}")

    def _export_csv(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Choose Export Folder")
        if not directory:
            return

        data = self._gather_data()
        tasks_path, habits_path = write_csv_export(data, Path(directory))
        QMessageBox.information(
            self, "Export Complete",
            f"Saved:\n{tasks_path.name}\n{habits_path.name}\n\nin {directory}"
        )