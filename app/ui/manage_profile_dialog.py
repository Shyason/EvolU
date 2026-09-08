from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from app.data.repository import ProfileRepository


class ManageProfileDialog(QDialog):
    def __init__(self, profile_id, profile_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Profile")
        self.setMinimumWidth(320)
        self.profile_id = profile_id
        self.profile_repo = ProfileRepository()
        self.was_deleted = False
        self.was_renamed = False

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Profile name:"))
        self.name_input = QLineEdit(profile_name)
        layout.addWidget(self.name_input)

        rename_button = QPushButton("Save Name")
        rename_button.setProperty("class", "primary")
        rename_button.clicked.connect(self._rename)
        layout.addWidget(rename_button)

        divider = QLabel("")
        divider.setFixedHeight(12)
        layout.addWidget(divider)

        warning = QLabel("Deleting a profile permanently removes all its tasks, habits, and history. This cannot be undone.")
        warning.setWordWrap(True)
        warning.setStyleSheet("color: #94A3B8; font-size: 12px;")
        layout.addWidget(warning)

        delete_button = QPushButton("Delete This Profile")
        delete_button.setStyleSheet("background-color: #DC2626; color: white; border: none;")
        delete_button.clicked.connect(self._delete)
        layout.addWidget(delete_button)

    def _rename(self):
        new_name = self.name_input.text().strip()
        if not new_name:
            return
        self.profile_repo.rename(self.profile_id, new_name)
        self.was_renamed = True
        self.accept()

    def _delete(self):
        confirm = QMessageBox.warning(
            self, "Delete Profile",
            "Are you sure you want to permanently delete this profile and all its data?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.profile_repo.delete(self.profile_id)
            self.was_deleted = True
            self.accept()
