from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.business.scheduling import describe_recurrence
from app.data.repository import HabitRepository
from app.ui.add_habit_dialog import AddHabitDialog
from app.ui.emoji_icon import render_emoji_icon
from app.ui.habit_heatmap_dialog import HabitHeatmapDialog

WEEKDAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
WEEKDAY_LETTERS = ["M", "T", "W", "T", "F", "S", "S"]


def habit_runs_on_weekday(habit, weekday_key):
    if habit.recurrence_type == "daily":
        return True
    if habit.recurrence_type == "weekdays":
        return weekday_key in habit.recurrence_params.get("days", [])
    return False


class WeekdayFilterBar(QWidget):
    day_selected = Signal(object)

    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 16)
        layout.setSpacing(8)

        self.buttons = {}

        all_button = QPushButton("All")
        all_button.setCheckable(True)
        all_button.setChecked(True)
        all_button.setFixedSize(56, 32)
        all_button.setContentsMargins(0, 0, 0, 0)
        all_button.clicked.connect(lambda: self._select(None))
        layout.addWidget(all_button)
        self.buttons[None] = all_button

        for key, letter in zip(WEEKDAY_KEYS, WEEKDAY_LETTERS):
            button = QPushButton(letter)
            button.setCheckable(True)
            button.setFixedSize(32, 32)
            button.setContentsMargins(0, 0, 0, 0)
            button.clicked.connect(lambda checked, k=key: self._select(k))
            layout.addWidget(button)
            self.buttons[key] = button

        layout.addStretch()
        self._apply_button_styles()

    def _select(self, key):
        for button_key, button in self.buttons.items():
            button.setChecked(button_key == key)
        self._apply_button_styles()
        self.day_selected.emit(key)

    def _apply_button_styles(self):
        for button_key, button in self.buttons.items():
            radius = "16px"
            if button.isChecked():
                button.setStyleSheet(
                    "background-color: #22C55E; color: #0F172A; border: none;"
                    "border-radius: " + radius + "; font-weight: 700; padding: 0px;"
                )
            else:
                button.setStyleSheet(
                    "background-color: transparent; color: #94A3B8;"
                    "border: 1.5px solid #2A3752; border-radius: " + radius + "; font-weight: 600; padding: 0px;"
                )


class AllHabitRow(QWidget):
    delete_requested = Signal(int)
    view_history_requested = Signal(int)
    edit_requested = Signal(int)

    def __init__(self, habit_id, title, tag_color, recurrence_desc, current_streak, longest_streak):
        super().__init__()
        self.habit_id = habit_id

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        color_dot = QLabel()
        color_dot.setFixedSize(10, 10)
        color_dot.setStyleSheet("background-color: " + tag_color + "; border-radius: 5px;")

        title_label = QLabel(title)
        recurrence_label = QLabel(recurrence_desc)
        recurrence_label.setStyleSheet("color: #94A3B8;")
        streak_label = QLabel("\U0001F525 " + str(current_streak) + "   \U0001F3C6 " + str(longest_streak))

        history_button = QPushButton()
        history_button.setIcon(render_emoji_icon("\U0001F4CA"))
        history_button.setFixedWidth(32)
        history_button.clicked.connect(lambda: self.view_history_requested.emit(self.habit_id))

        edit_button = QPushButton("Edit")
        edit_button.clicked.connect(lambda: self.edit_requested.emit(self.habit_id))

        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(lambda: self.delete_requested.emit(self.habit_id))

        layout.addWidget(color_dot)
        layout.addWidget(title_label, 1)
        layout.addWidget(recurrence_label)
        layout.addWidget(streak_label)
        layout.addWidget(history_button)
        layout.addWidget(edit_button)
        layout.addWidget(delete_button)


class AllHabitsWidget(QWidget):
    data_changed = Signal()

    def __init__(self):
        super().__init__()
        self.habit_repo = HabitRepository()
        self.current_profile_id = None
        self.selected_weekday = None

        outer_layout = QVBoxLayout(self)
        outer_layout.addWidget(QLabel("<h2>All Habits</h2>"))

        self.filter_bar = WeekdayFilterBar()
        self.filter_bar.day_selected.connect(self._on_day_selected)
        outer_layout.addWidget(self.filter_bar)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        self.rows_layout = QVBoxLayout(scroll_content)
        self.rows_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        outer_layout.addWidget(scroll_area, 1)

        self.empty_label = QLabel("No habits yet. Press Ctrl+H to add one.")
        outer_layout.addWidget(self.empty_label)
        self.empty_label.hide()

    def load_for_profile(self, profile_id):
        self.current_profile_id = profile_id
        self.refresh()

    def _on_day_selected(self, weekday_key):
        self.selected_weekday = weekday_key
        self.refresh()

    def refresh(self):
        while self.rows_layout.count() > 1:
            item = self.rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if self.current_profile_id is None:
            return

        habits = self.habit_repo.get_all(self.current_profile_id)
        if self.selected_weekday is not None:
            habits = [h for h in habits if habit_runs_on_weekday(h, self.selected_weekday)]

        for habit in habits:
            tag_color = habit.tag.color_hex if habit.tag else "#888888"
            recurrence_desc = describe_recurrence(habit.recurrence_type, habit.recurrence_params)
            row = AllHabitRow(
                habit.id, habit.title, tag_color, recurrence_desc,
                habit.current_streak, habit.longest_streak,
            )
            row.delete_requested.connect(self._on_delete_requested)
            row.view_history_requested.connect(self._on_view_history_requested)
            row.edit_requested.connect(self._on_edit_requested)
            self.rows_layout.insertWidget(self.rows_layout.count() - 1, row)

        self.empty_label.setVisible(len(habits) == 0)

    def _on_delete_requested(self, habit_id):
        self.habit_repo.delete(habit_id)
        self.refresh()
        self.data_changed.emit()

    def _on_view_history_requested(self, habit_id):
        dialog = HabitHeatmapDialog(habit_id, self)
        dialog.exec()

    def _on_edit_requested(self, habit_id):
        habit = self.habit_repo.get_by_id(habit_id)
        if habit is None:
            return
        from PySide6.QtWidgets import QDialog, QApplication
        dialog = AddHabitDialog(self.current_profile_id, self, habit=habit)
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted or getattr(dialog, "tags_changed", False):
            self.refresh()
            self.data_changed.emit()
        QApplication.processEvents()