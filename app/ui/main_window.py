from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtGui import QKeySequence, QShortcut, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.business.notification_service import NotificationService
from app.data.focus_repository import FocusRepository
from app.data.repository import ProfileRepository
from app.ui.achievements_dialog import AchievementsDialog
from app.ui.add_habit_dialog import AddHabitDialog
from app.ui.add_task_dialog import AddTaskDialog
from app.ui.all_habits_widget import AllHabitsWidget
from app.ui.all_tasks_widget import AllTasksWidget
from app.ui.analytics_widget import AnalyticsWidget
from app.ui.dashboard_widget import DashboardWidget
from app.ui.emoji_icon import render_emoji_icon
from app.ui.export_dialog import ExportDialog
from app.ui.focus_timer_dialog import FocusTimerDialog
from app.ui.notification_bell import NotificationBell
from app.ui.review_widget import ReviewWidget
from app.ui.theme import DARK, build_stylesheet
from app.ui.xp_bar_widget import XPBarWidget
from app.ui.manage_profile_dialog import ManageProfileDialog

TAB_LABELS = ["Today", "All Tasks", "All Habits", "Analytics", "Review"]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EvolU \u2014 Your Evolution, Every Day.")
        self.setWindowIcon(QIcon("app/ui/icons/app_icon.png"))
        self.resize(1100, 700)

        self.profile_repo = ProfileRepository()
        self.focus_repo = FocusRepository()
        self.current_profile = None

        self.active_focus_session_id = None
        self.focus_elapsed_seconds = 0
        self.focus_timer = QTimer(self)
        self.focus_timer.timeout.connect(self._focus_tick)
        self.focus_timer_dialog = None

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # --- Profile bar (top row) ---
        profile_bar = QHBoxLayout()

        self.profile_selector = QComboBox()
        self.xp_bar = XPBarWidget()
        self.new_profile_button = QPushButton("+ New Profile")
        self.add_task_button = QPushButton("+ Task")
        self.add_habit_button = QPushButton("+ Habit")
        self.export_button = QPushButton("Export")

        self.focus_button = QPushButton()
        self.focus_button.setIcon(render_emoji_icon("\u23F1"))
        self.focus_button.setFixedWidth(40)

        self.notification_bell = NotificationBell()

        self.achievements_button = QPushButton()
        self.achievements_button.setIcon(render_emoji_icon("\U0001F3C6"))
        self.achievements_button.setFixedWidth(40)

        self.manage_profile_button = QPushButton()
        self.manage_profile_button.setIcon(render_emoji_icon("\u2699"))
        self.manage_profile_button.setFixedWidth(36)

        profile_bar.addWidget(QLabel("Profile:"))
        profile_bar.addWidget(self.profile_selector)
        profile_bar.addWidget(self.manage_profile_button)
        profile_bar.addWidget(self.xp_bar)
        profile_bar.addWidget(self.new_profile_button)
        profile_bar.addWidget(self.add_task_button)
        profile_bar.addWidget(self.add_habit_button)
        profile_bar.addWidget(self.export_button)
        profile_bar.addWidget(self.focus_button)
        profile_bar.addWidget(self.notification_bell)
        profile_bar.addWidget(self.achievements_button)
        profile_bar.addStretch()

        main_layout.addLayout(profile_bar)

        # --- Sidebar + content area ---
        content_row = QHBoxLayout()
        content_row.setSpacing(0)

        self.sidebar = QListWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(190)
        for label in TAB_LABELS:
            QListWidgetItem(label, self.sidebar)

        self.stack = QStackedWidget()
        self.dashboard = DashboardWidget()
        self.all_tasks = AllTasksWidget()
        self.all_habits = AllHabitsWidget()
        self.analytics = AnalyticsWidget()
        self.review = ReviewWidget()

        self.stack.addWidget(self.dashboard)
        self.stack.addWidget(self.all_tasks)
        self.stack.addWidget(self.all_habits)
        self.stack.addWidget(self.analytics)
        self.stack.addWidget(self.review)

        content_row.addWidget(self.sidebar)
        content_row.addWidget(self.stack, 1)
        main_layout.addLayout(content_row, 1)

        self.sidebar.currentRowChanged.connect(self._on_tab_changed)
        self.sidebar.setCurrentRow(0)

        # --- Keep tabs in sync with each other ---
        self.all_tasks.data_changed.connect(self.dashboard.refresh)
        self.dashboard.data_changed.connect(self.all_tasks.refresh)
        self.all_habits.data_changed.connect(self.dashboard.refresh)
        self.dashboard.xp_changed.connect(self.xp_bar.refresh)

        # --- Keyboard shortcuts ---
        self.add_task_shortcut = QShortcut(QKeySequence("Ctrl+T"), self)
        self.add_task_shortcut.activated.connect(self.handle_add_task)

        self.add_habit_shortcut = QShortcut(QKeySequence("Ctrl+H"), self)
        self.add_habit_shortcut.activated.connect(self.handle_add_habit)

        self.new_profile_shortcut = QShortcut(QKeySequence("Ctrl+P"), self)
        self.new_profile_shortcut.activated.connect(self.handle_new_profile)

        self.export_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        self.export_shortcut.activated.connect(self.handle_export)

        self.manage_profile_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        self.manage_profile_shortcut.activated.connect(self.handle_manage_profile)

        # --- Button connections ---
        self.new_profile_button.clicked.connect(self.handle_new_profile)
        self.profile_selector.currentIndexChanged.connect(self.handle_profile_changed)
        self.add_task_button.clicked.connect(self.handle_add_task)
        self.add_habit_button.clicked.connect(self.handle_add_habit)
        self.export_button.clicked.connect(self.handle_export)
        self.focus_button.clicked.connect(self.handle_focus_timer)
        self.achievements_button.clicked.connect(self.handle_achievements)
        self.manage_profile_button.clicked.connect(self.handle_manage_profile)

        # --- Notifications ---
        self.notification_service = NotificationService()
        self.notification_timer = QTimer(self)
        self.notification_timer.timeout.connect(self._check_notifications)
        self.notification_timer.start(60_000)

        self.load_profiles()
        self._apply_theme()

    def load_profiles(self) -> None:
        profiles = self.profile_repo.get_all()
        if not profiles:
            default_profile = self.profile_repo.create("Default")
            profiles = [default_profile]

        self.profile_selector.clear()
        for profile in profiles:
            self.profile_selector.addItem(profile.name, userData=profile.id)

        self.current_profile = profiles[0]

    def handle_new_profile(self) -> None:
        name, ok = QInputDialog.getText(self, "New Profile", "Profile name:")
        if ok and name.strip():
            self.profile_repo.create(name.strip())
            self.load_profiles()
            self.profile_selector.setCurrentIndex(self.profile_selector.count() - 1)

    def handle_profile_changed(self, index: int) -> None:
        if index < 0:
            return
        profile_id = self.profile_selector.itemData(index)
        self.current_profile = self.profile_repo.get_by_id(profile_id)
        self._apply_theme()
        self.dashboard.load_for_profile(profile_id)
        self.all_tasks.load_for_profile(profile_id)
        self.all_habits.load_for_profile(profile_id)
        self.analytics.load_for_profile(profile_id)
        self.review.load_for_profile(profile_id)
        self.notification_bell.set_profile(profile_id)
        self.xp_bar.set_profile(profile_id)

    def handle_manage_profile(self) -> None:
        if self.current_profile is None:
            return
        dialog = ManageProfileDialog(self.current_profile.id, self.current_profile.name, self)
        dialog.exec()
        if dialog.was_deleted:
            self.load_profiles()
            self.profile_selector.setCurrentIndex(0)
        elif dialog.was_renamed:
            self.load_profiles()
            index = self.profile_selector.findData(self.current_profile.id)
            if index >= 0:
                self.profile_selector.setCurrentIndex(index)

    def handle_add_task(self) -> None:
        dialog = AddTaskDialog(self.current_profile.id, self)
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            self.dashboard.refresh()
            self.all_tasks.refresh()
        elif getattr(dialog, "tags_changed", False):
            self.dashboard.refresh()
            self.all_tasks.refresh()
            self.all_habits.refresh()
        QApplication.processEvents()

    def handle_add_habit(self) -> None:
        dialog = AddHabitDialog(self.current_profile.id, self)
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            self.dashboard.refresh()
            self.all_habits.refresh()
        elif getattr(dialog, "tags_changed", False):
            self.dashboard.refresh()
            self.all_tasks.refresh()
            self.all_habits.refresh()
        QApplication.processEvents()

    def handle_export(self) -> None:
        dialog = ExportDialog(self.current_profile.id, self)
        dialog.exec()

    def handle_focus_timer(self) -> None:
        if self.focus_timer_dialog is None or not self.focus_timer_dialog.isVisible():
            self.focus_timer_dialog = FocusTimerDialog(self)
            self.focus_timer_dialog.show()
        else:
            self.focus_timer_dialog.raise_()
            self.focus_timer_dialog.activateWindow()

    def toggle_focus_session(self) -> None:
        if self.active_focus_session_id is None:
            focus_session = self.focus_repo.start_session(self.current_profile.id)
            self.active_focus_session_id = focus_session.id
            self.focus_elapsed_seconds = 0
            self.focus_timer.start(1000)
            self.focus_button.setStyleSheet("background-color: #22C55E;")
        else:
            self.focus_timer.stop()
            self.focus_repo.stop_session(self.active_focus_session_id)
            self.active_focus_session_id = None
            self.focus_button.setStyleSheet("")

    def reset_focus_session(self) -> None:
        if self.active_focus_session_id is not None:
            self.focus_repo.discard_session(self.active_focus_session_id)
            self.active_focus_session_id = None
            self.focus_timer.stop()
            self.focus_button.setStyleSheet("")
        self.focus_elapsed_seconds = 0
        if self.focus_timer_dialog and self.focus_timer_dialog.isVisible():
            self.focus_timer_dialog.update_display(0)

    def _focus_tick(self) -> None:
        self.focus_elapsed_seconds += 1
        if self.focus_timer_dialog and self.focus_timer_dialog.isVisible():
            self.focus_timer_dialog.update_display(self.focus_elapsed_seconds)

    def handle_achievements(self) -> None:
        dialog = AchievementsDialog(self.current_profile.id, self)
        dialog.exec()

    def _apply_theme(self) -> None:
        heading_font = getattr(self, "_heading_font", "Plus Jakarta Sans")
        body_font = getattr(self, "_body_font", "Plus Jakarta Sans")
        QApplication.instance().setStyleSheet(build_stylesheet(DARK, heading_font, body_font))

    def _on_tab_changed(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        widget = self.stack.widget(index)
        if widget in (self.analytics, self.review) and self.current_profile:
            widget.refresh()

    def _check_notifications(self) -> None:
        if self.current_profile:
            self.notification_service.check_and_fire(self.current_profile.id)
            self.notification_bell.refresh_count()

    def closeEvent(self, event) -> None:
        if self.active_focus_session_id is not None:
            self.focus_repo.stop_session(self.active_focus_session_id)
        event.accept()
