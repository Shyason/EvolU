from __future__ import annotations

import datetime as dt

from PySide6.QtCore import QDate, QTime
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QTimeEdit,
    QVBoxLayout,
)

from app.data.repository import TagRepository, TaskRepository
from app.ui.tag_dialog import NewTagDialog
from app.ui.manage_tags_dialog import ManageTagsDialog

NEW_TAG_SENTINEL = "+ New Tag..."


class AddTaskDialog(QDialog):
    def __init__(self, profile_id: int, parent=None, task=None):
        super().__init__(parent)
        self.editing_task = task
        self.setWindowTitle("Edit Task" if task else "Add Task")
        self.profile_id = profile_id
        self.task_repo = TaskRepository()
        self.tag_repo = TagRepository()

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.title_input = QLineEdit()
        form.addRow("Title:", self.title_input)

        due_date_row = QHBoxLayout()
        self.has_due_date = QCheckBox("Set due date")
        self.date_input = QDateEdit(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setEnabled(False)
        self.has_due_date.toggled.connect(self.date_input.setEnabled)
        due_date_row.addWidget(self.has_due_date)
        due_date_row.addWidget(self.date_input)
        form.addRow(due_date_row)

        due_time_row = QHBoxLayout()
        self.has_due_time = QCheckBox("Set due time")
        self.time_input = QTimeEdit(QTime.currentTime())
        self.time_input.setEnabled(False)
        self.has_due_time.toggled.connect(self.time_input.setEnabled)
        due_time_row.addWidget(self.has_due_time)
        due_time_row.addWidget(self.time_input)
        form.addRow(due_time_row)

        self.priority_input = QComboBox()
        self.priority_input.addItems(["low", "medium", "high"])
        self.priority_input.setCurrentText("medium")
        form.addRow("Priority:", self.priority_input)

        repeat_row = QHBoxLayout()
        self.is_recurring_checkbox = QCheckBox("Repeats")
        self.recurrence_type_input = QComboBox()
        self.recurrence_type_input.addItems(["daily", "weekly", "monthly"])
        self.recurrence_type_input.setEnabled(False)
        self.is_recurring_checkbox.toggled.connect(self.recurrence_type_input.setEnabled)
        repeat_row.addWidget(self.is_recurring_checkbox)
        repeat_row.addWidget(self.recurrence_type_input)
        form.addRow(repeat_row)

        self.tag_input = QComboBox()
        self._reload_tags()
        self.tag_input.currentTextChanged.connect(self._handle_tag_selection)
        form.addRow("Tag:", self.tag_input)

        self.notes_input = QTextEdit()
        self.notes_input.setFixedHeight(60)
        form.addRow("Notes:", self.notes_input)

        layout.addLayout(form)

        save_button = QPushButton("Save Changes" if task else "Add Task")
        save_button.setProperty("class", "primary")
        save_button.clicked.connect(self.save)
        layout.addWidget(save_button)

        if task:
            self.title_input.setText(task.title)
            if task.due_date:
                self.has_due_date.setChecked(True)
                self.date_input.setDate(QDate(task.due_date.year, task.due_date.month, task.due_date.day))
            if task.due_time:
                self.has_due_time.setChecked(True)
                self.time_input.setTime(QTime(task.due_time.hour, task.due_time.minute))
            self.priority_input.setCurrentText(task.priority)
            if task.tag_id:
                index = self.tag_input.findData(task.tag_id)
                if index >= 0:
                    self.tag_input.setCurrentIndex(index)
            if task.notes:
                self.notes_input.setPlainText(task.notes)

            if task.is_recurring:
                self.is_recurring_checkbox.setChecked(True)
                self.recurrence_type_input.setEnabled(True)
                if task.recurrence_type:
                    index = self.recurrence_type_input.findText(task.recurrence_type)
                    if index >= 0:
                        self.recurrence_type_input.setCurrentIndex(index)

    def _reload_tags(self) -> None:
        self.tag_input.blockSignals(True)  # avoid re-triggering the selection handler while rebuilding
        self.tag_input.clear()
        self.tag_input.addItem("(none)", userData=None)
        for tag in self.tag_repo.get_for_profile(self.profile_id):
            self.tag_input.addItem(tag.name, userData=tag.id)
        self.tag_input.addItem(NEW_TAG_SENTINEL, userData="new")
        self.tag_input.addItem("\u2699 Manage Tags...", userData="manage")
        self.tag_input.blockSignals(False)

    def _handle_tag_selection(self, text: str) -> None:
        if text == NEW_TAG_SENTINEL:
            dialog = NewTagDialog(self.profile_id, self)
            if dialog.exec() == QDialog.DialogCode.Accepted and dialog.created_tag:
                self._reload_tags()
                index = self.tag_input.findData(dialog.created_tag.id)
                self.tag_input.setCurrentIndex(index)
            else:
                self.tag_input.setCurrentIndex(0)
        elif text.startswith("\u2699"):
            dialog = ManageTagsDialog(self.profile_id, self)
            dialog.exec()
            self._reload_tags()
            self.tag_input.setCurrentIndex(0)

    def save(self) -> None:
        title = self.title_input.text().strip()
        if not title:
            return

        if self.has_due_date.isChecked():
            due_date = self.date_input.date().toPython()
        elif self.is_recurring_checkbox.isChecked():
            due_date = dt.date.today()
        else:
            due_date = None
        due_time = self.time_input.time().toPython() if self.has_due_time.isChecked() else None
        tag_id = self.tag_input.currentData()
        if tag_id in ("new", "manage"):
            tag_id = None

        fields = dict(
            title=title,
            due_date=due_date,
            due_time=due_time,
            priority=self.priority_input.currentText(),
            tag_id=tag_id,
            notes=self.notes_input.toPlainText().strip() or None,
            is_recurring=self.is_recurring_checkbox.isChecked(),
            recurrence_type=self.recurrence_type_input.currentText() if self.is_recurring_checkbox.isChecked() else None,
            recurrence_interval=1,
        )

        if self.editing_task:
            self.task_repo.update(self.editing_task.id, **fields)
        else:
            self.task_repo.create(self.profile_id, **fields)
        self.accept()