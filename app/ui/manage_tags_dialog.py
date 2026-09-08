from __future__ import annotations

from PySide6.QtWidgets import (
    QColorDialog,
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.data.repository import HabitRepository, TagRepository, TaskRepository


class TagRow(QWidget):
    def __init__(self, tag, on_changed):
        super().__init__()
        self.tag = tag
        self.tag_repo = TagRepository()
        self.on_changed = on_changed

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.color_button = QPushButton()
        self.color_button.setFixedSize(24, 24)
        self.color_button.setStyleSheet("background-color: " + tag.color_hex + "; border-radius: 12px; border: none;")
        self.color_button.clicked.connect(self._pick_color)

        self.name_label = QLabel(tag.name)

        rename_button = QPushButton("Rename")
        rename_button.clicked.connect(self._rename)

        delete_button = QPushButton("Delete")
        delete_button.setStyleSheet("background-color: #DC2626; color: white; border: none;")
        delete_button.clicked.connect(self._delete)

        layout.addWidget(self.color_button)
        layout.addWidget(self.name_label, 1)
        layout.addWidget(rename_button)
        layout.addWidget(delete_button)

    def _pick_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.tag_repo.update(self.tag.id, color_hex=color.name())
            self.color_button.setStyleSheet(
                "background-color: " + color.name() + "; border-radius: 12px; border: none;"
            )

    def _rename(self):
        new_name, ok = QInputDialog.getText(self, "Rename Tag", "New name:", text=self.tag.name)
        if ok and new_name.strip():
            self.tag_repo.update(self.tag.id, name=new_name.strip())
            self.name_label.setText(new_name.strip())

    def _delete(self):
        confirm = QMessageBox.warning(
            self, "Delete Tag",
            "Delete \"" + self.tag.name + "\"? Tasks and habits using it will become untagged.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            task_repo = TaskRepository()
            habit_repo = HabitRepository()
            for task in task_repo.get_all(self.tag.profile_id):
                if task.tag_id == self.tag.id:
                    task_repo.update(task.id, tag_id=None)
            for habit in habit_repo.get_all(self.tag.profile_id):
                if habit.tag_id == self.tag.id:
                    habit_repo.update(habit.id, tag_id=None)
            self.tag_repo.delete(self.tag.id)
            self.on_changed()


class ManageTagsDialog(QDialog):
    def __init__(self, profile_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Tags")
        self.setMinimumSize(380, 400)
        self.profile_id = profile_id
        self.tag_repo = TagRepository()

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h3>Manage Tags</h3>"))

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.addStretch()
        scroll_area.setWidget(self.content)
        layout.addWidget(scroll_area, 1)

        self._load_tags()

    def _load_tags(self):
        while self.content_layout.count() > 1:
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        tags = self.tag_repo.get_for_profile(self.profile_id)
        if not tags:
            self.content_layout.insertWidget(0, QLabel("No tags yet."))
        for tag in tags:
            row = TagRow(tag, self._load_tags)
            self.content_layout.insertWidget(self.content_layout.count() - 1, row)
