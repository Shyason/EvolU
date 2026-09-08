from __future__ import annotations

import datetime as dt

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QApplication,
)

from app.data.repository import TaskRepository
from app.ui.add_task_dialog import AddTaskDialog


class AllTaskRow(QWidget):
    toggled = Signal(int, bool)
    delete_requested = Signal(int)
    edit_requested = Signal(int)

    def __init__(self, task_id, title, tag_color, is_completed, due_date, priority, is_overdue):
        super().__init__()
        self.task_id = task_id

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(is_completed)
        self.checkbox.stateChanged.connect(self._on_toggled)

        color_dot = QLabel()
        color_dot.setFixedSize(10, 10)
        color_dot.setStyleSheet("background-color: " + tag_color + "; border-radius: 5px;")

        self.title_label = QLabel(title)
        self._apply_title_style(is_completed, is_overdue)

        due_text = due_date.strftime("%b %d") if due_date else "No due date"
        due_label = QLabel(due_text)
        if is_overdue:
            due_label.setStyleSheet("color: #FB7185; font-weight: bold;")

        priority_label = QLabel(priority.capitalize())

        edit_button = QPushButton("Edit")
        edit_button.clicked.connect(lambda: self.edit_requested.emit(self.task_id))

        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(lambda: self.delete_requested.emit(self.task_id))

        layout.addWidget(self.checkbox)
        layout.addWidget(color_dot)
        layout.addWidget(self.title_label, 1)
        layout.addWidget(due_label)
        layout.addWidget(priority_label)
        layout.addWidget(edit_button)
        layout.addWidget(delete_button)

    def _apply_title_style(self, is_completed, is_overdue):
        if is_completed:
            self.title_label.setStyleSheet("text-decoration: line-through; color: gray;")
        elif is_overdue:
            self.title_label.setStyleSheet("color: #FB7185;")
        else:
            self.title_label.setStyleSheet("")

    def _on_toggled(self, state):
        is_checked = bool(state)
        self._apply_title_style(is_checked, False)
        self.toggled.emit(self.task_id, is_checked)


class SectionHeader(QLabel):
    def __init__(self, text, dim=True):
        super().__init__(text)
        color = "#64748B" if dim else "#94A3B8"
        self.setStyleSheet("color: " + color + "; font-weight: 700; font-size: 13px; padding-top: 12px;")


class CollapsibleHeader(QPushButton):
    toggled_open = Signal(bool)

    def __init__(self, count):
        super().__init__()
        self.is_open = False
        self._count = count
        self.setCheckable(True)
        self.setChecked(False)
        self._update_text()
        self.setStyleSheet(
            "text-align: left; background: transparent; border: none;"
            "color: #64748B; font-weight: 700; font-size: 13px; padding: 12px 0px;"
        )
        self.clicked.connect(self._on_clicked)

    def _update_text(self):
        arrow = "\u25BE" if self.is_open else "\u25B8"
        self.setText(arrow + "  Completed (" + str(self._count) + ")")

    def _on_clicked(self):
        self.is_open = not self.is_open
        self._update_text()
        self.toggled_open.emit(self.is_open)


class AllTasksWidget(QWidget):
    data_changed = Signal()

    def __init__(self):
        super().__init__()
        self.task_repo = TaskRepository()
        self.current_profile_id = None
        self.completed_open = False

        outer_layout = QVBoxLayout(self)
        outer_layout.addWidget(QLabel("<h2>All Tasks</h2>"))

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        self.rows_layout = QVBoxLayout(scroll_content)
        self.rows_layout.setSpacing(6)
        self.rows_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        outer_layout.addWidget(scroll_area, 1)

        self.empty_label = QLabel("No tasks yet. Click + Task to add one.")
        outer_layout.addWidget(self.empty_label)
        self.empty_label.hide()

    def load_for_profile(self, profile_id):
        self.current_profile_id = profile_id
        self.refresh()

    def refresh(self):
        while self.rows_layout.count() > 1:
            item = self.rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if self.current_profile_id is None:
            return

        today = dt.date.today()
        all_tasks = self.task_repo.get_all(self.current_profile_id)
        priority_order = {"high": 0, "medium": 1, "low": 2}

        active_tasks = [t for t in all_tasks if not t.is_completed]
        completed_tasks = [t for t in all_tasks if t.is_completed]

        def sort_key(task):
            is_overdue = task.due_date is not None and task.due_date < today
            return (not is_overdue, priority_order.get(task.priority, 1), task.due_date or dt.date.max)

        buckets = {}
        for task in active_tasks:
            buckets.setdefault(task.due_date, []).append(task)
        for key in buckets:
            buckets[key].sort(key=sort_key)

        dated_keys = sorted(k for k in buckets if k is not None)
        ordered_keys = []
        if today in dated_keys:
            ordered_keys.append(today)
            dated_keys.remove(today)
        ordered_keys.extend(dated_keys)
        if None in buckets:
            ordered_keys.append(None)

        for key in ordered_keys:
            if key == today:
                header = SectionHeader("Today", dim=True)
            elif key is None:
                header = SectionHeader("No due date", dim=True)
            else:
                header = SectionHeader(key.strftime("%A, %b %d"), dim=False)
            self.rows_layout.insertWidget(self.rows_layout.count() - 1, header)

            for task in buckets[key]:
                is_overdue = task.due_date is not None and task.due_date < today
                self._add_row(task, is_overdue)

        completed_tasks.sort(key=lambda t: t.completed_at or dt.datetime.min, reverse=True)
        completed_header = CollapsibleHeader(len(completed_tasks))
        completed_header.is_open = self.completed_open
        completed_header._update_text()
        completed_header.toggled_open.connect(self._on_completed_toggled)
        self.rows_layout.insertWidget(self.rows_layout.count() - 1, completed_header)

        if self.completed_open:
            for task in completed_tasks:
                self._add_row(task, False)

        self.empty_label.setVisible(len(all_tasks) == 0)

    def _add_row(self, task, is_overdue):
        tag_color = task.tag.color_hex if task.tag else "#888888"
        row = AllTaskRow(
            task.id, task.title, tag_color, task.is_completed,
            task.due_date, task.priority, is_overdue,
        )
        row.toggled.connect(self._on_row_toggled)
        row.delete_requested.connect(self._on_delete_requested)
        row.edit_requested.connect(self._on_edit_requested)
        self.rows_layout.insertWidget(self.rows_layout.count() - 1, row)

    def _on_completed_toggled(self, is_open):
        self.completed_open = is_open
        self.refresh()

    def _on_row_toggled(self, task_id, is_checked):
        self.task_repo.toggle_complete(task_id)
        self.refresh()
        self.data_changed.emit()

    def _on_delete_requested(self, task_id):
        self.task_repo.delete(task_id)
        self.refresh()
        self.data_changed.emit()

    def _on_edit_requested(self, task_id):
        task = self.task_repo.get_by_id(task_id)
        if task is None:
            return
        dialog = AddTaskDialog(self.current_profile_id, self, task=task)
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted or getattr(dialog, "tags_changed", False):
            self.refresh()
            self.data_changed.emit()
        QApplication.processEvents()