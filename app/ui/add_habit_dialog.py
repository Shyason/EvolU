from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.data.repository import HabitRepository, TagRepository
from app.ui.manage_tags_dialog import ManageTagsDialog
from app.ui.tag_dialog import NewTagDialog

NEW_TAG_SENTINEL = "+ New Tag..."
MANAGE_TAG_SENTINEL = "\u2699 Manage Tags..."
WEEKDAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class AddHabitDialog(QDialog):
    def __init__(self, profile_id, parent=None, habit=None):
        super().__init__(parent)
        self.editing_habit = habit
        self.tags_changed = False
        self.setWindowTitle("Edit Habit" if habit else "Add Habit")
        self.setFixedWidth(360)
        self.profile_id = profile_id
        self.habit_repo = HabitRepository()
        self.tag_repo = TagRepository()

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.title_input = QLineEdit()
        form.addRow("Title:", self.title_input)

        self.recurrence_type = QComboBox()
        self.recurrence_type.addItem("Daily", userData="daily")
        self.recurrence_type.addItem("Specific weekdays", userData="weekdays")
        form.addRow("Repeats:", self.recurrence_type)

        self.recurrence_stack = QStackedWidget()

        empty_page = QWidget()
        self.recurrence_stack.addWidget(empty_page)

        weekdays_page = QWidget()
        weekdays_layout = QHBoxLayout(weekdays_page)
        self.weekday_checkboxes = {}
        for key, label in zip(WEEKDAY_KEYS, WEEKDAY_LABELS):
            checkbox = QCheckBox(label)
            self.weekday_checkboxes[key] = checkbox
            weekdays_layout.addWidget(checkbox)
        self.recurrence_stack.addWidget(weekdays_page)

        self.recurrence_type.currentIndexChanged.connect(self.recurrence_stack.setCurrentIndex)
        form.addRow("", self.recurrence_stack)

        self.tag_input = QComboBox()
        self._reload_tags()
        self.tag_input.currentTextChanged.connect(self._handle_tag_selection)
        form.addRow("Tag:", self.tag_input)

        self.notes_input = QTextEdit()
        self.notes_input.setFixedHeight(60)
        form.addRow("Notes:", self.notes_input)

        layout.addLayout(form)

        save_button = QPushButton("Save Changes" if habit else "Add Habit")
        save_button.setProperty("class", "primary")
        save_button.clicked.connect(self.save)
        layout.addWidget(save_button)

        if habit:
            self.title_input.setText(habit.title)

            recurrence_index = self.recurrence_type.findData(habit.recurrence_type)
            if recurrence_index >= 0:
                self.recurrence_type.setCurrentIndex(recurrence_index)
            else:
                self.recurrence_type.setCurrentIndex(0)
            if habit.recurrence_type == "weekdays":
                for key in habit.recurrence_params.get("days", []):
                    if key in self.weekday_checkboxes:
                        self.weekday_checkboxes[key].setChecked(True)

            if habit.tag_id:
                index = self.tag_input.findData(habit.tag_id)
                if index >= 0:
                    self.tag_input.setCurrentIndex(index)
            if habit.notes:
                self.notes_input.setPlainText(habit.notes)

    def _reload_tags(self):
        self.tag_input.blockSignals(True)
        self.tag_input.clear()
        self.tag_input.addItem("(none)", userData=None)
        for tag in self.tag_repo.get_for_profile(self.profile_id):
            self.tag_input.addItem(tag.name, userData=tag.id)
        self.tag_input.addItem(NEW_TAG_SENTINEL, userData="new")
        self.tag_input.addItem(MANAGE_TAG_SENTINEL, userData="manage")
        self.tag_input.blockSignals(False)

    def _handle_tag_selection(self, text):
        if text == NEW_TAG_SENTINEL:
            dialog = NewTagDialog(self.profile_id, self)
            if dialog.exec() == QDialog.DialogCode.Accepted and dialog.created_tag:
                self._reload_tags()
                index = self.tag_input.findData(dialog.created_tag.id)
                self.tag_input.setCurrentIndex(index)
            else:
                self.tag_input.setCurrentIndex(0)
        elif text == MANAGE_TAG_SENTINEL:
            dialog = ManageTagsDialog(self.profile_id, self)
            dialog.exec()
            self._reload_tags()
            self.tag_input.setCurrentIndex(0)
            self.tags_changed = True

    def save(self):
        title = self.title_input.text().strip()
        if not title:
            return

        recurrence_type = self.recurrence_type.currentData()
        if recurrence_type == "weekdays":
            recurrence_params = {
                "days": [key for key, box in self.weekday_checkboxes.items() if box.isChecked()]
            }
        else:
            recurrence_params = {}

        tag_id = self.tag_input.currentData()
        if tag_id in ("new", "manage"):
            tag_id = None

        fields = dict(
            title=title,
            recurrence_type=recurrence_type,
            recurrence_params=recurrence_params,
            streak_rule_type="strict",
            streak_rule_params={},
            tag_id=tag_id,
            notes=self.notes_input.toPlainText().strip() or None,
        )

        if self.editing_habit:
            self.habit_repo.update(self.editing_habit.id, **fields)
        else:
            self.habit_repo.create(self.profile_id, **fields)
        self.accept()
