from __future__ import annotations

from PySide6.QtWidgets import QColorDialog, QDialog, QFormLayout, QLineEdit, QPushButton, QVBoxLayout

from app.data.repository import TagRepository


class NewTagDialog(QDialog):
    def __init__(self, profile_id: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Tag")
        self.profile_id = profile_id
        self.tag_repo = TagRepository()
        self.created_tag = None
        self.selected_color = "#888888"

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_input = QLineEdit()
        form.addRow("Name:", self.name_input)

        self.color_button = QPushButton("Choose Color")
        self.color_button.clicked.connect(self.pick_color)
        form.addRow("Color:", self.color_button)

        layout.addLayout(form)

        save_button = QPushButton("Create Tag")
        save_button.setProperty("class", "primary")
        save_button.clicked.connect(self.save)
        layout.addWidget(save_button)

    def pick_color(self) -> None:
        color = QColorDialog.getColor()
        if color.isValid():
            self.selected_color = color.name()  # e.g. "#4caf50"
            self.color_button.setStyleSheet(f"background-color: {self.selected_color};")

    def save(self) -> None:
        name = self.name_input.text().strip()
        if not name:
            return
        self.created_tag = self.tag_repo.create(self.profile_id, name, self.selected_color)
        self.accept()  # closes the dialog, signaling success