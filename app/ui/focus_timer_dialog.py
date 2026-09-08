from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from app.ui.countdown_ring_widget import CountdownRingWidget


class FocusTimerDialog(QDialog):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.setWindowTitle("Focus Timer")
        self.setMinimumWidth(320)
        self.main_window = main_window

        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self._countdown_tick)
        self.countdown_total_seconds = 0
        self.countdown_remaining_seconds = 0
        self.countdown_running = False
        self.countdown_paused = False

        layout = QVBoxLayout(self)

        # --- Section 1: open-ended focus session (unchanged behavior) ---
        layout.addWidget(QLabel("<b>Focus Session</b>"))

        self.time_label = QLabel(self._format(main_window.focus_elapsed_seconds))
        self.time_label.setProperty("class", "heading")
        layout.addWidget(self.time_label)

        button_row = QHBoxLayout()
        is_running = main_window.active_focus_session_id is not None
        self.toggle_button = QPushButton("Stop Focus Session" if is_running else "Start Focus Session")
        self.toggle_button.setProperty("class", "primary")
        self.toggle_button.clicked.connect(self._toggle)
        button_row.addWidget(self.toggle_button)

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self._reset)
        button_row.addWidget(self.reset_button)
        layout.addLayout(button_row)

        hint = QLabel("You can close this window \u2014 the session keeps running.")
        hint.setProperty("class", "caption")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        divider = QLabel("")
        divider.setFixedHeight(20)
        layout.addWidget(divider)

        # --- Section 2: quick countdown timer ---
        layout.addWidget(QLabel("<b>Quick Timer</b>"))

        self.ring = CountdownRingWidget()
        ring_row = QHBoxLayout()
        ring_row.addStretch()
        ring_row.addWidget(self.ring)
        ring_row.addStretch()
        layout.addLayout(ring_row)

        setup_row = QHBoxLayout()
        setup_row.addWidget(QLabel("Minutes:"))
        self.minutes_input = QSpinBox()
        self.minutes_input.setRange(1, 180)
        self.minutes_input.setValue(5)
        setup_row.addWidget(self.minutes_input)
        layout.addLayout(setup_row)

        countdown_button_row = QHBoxLayout()
        self.start_countdown_button = QPushButton("Start Timer")
        self.start_countdown_button.setProperty("class", "primary")
        self.start_countdown_button.clicked.connect(self._handle_start_pause_resume)
        countdown_button_row.addWidget(self.start_countdown_button)

        self.cancel_countdown_button = QPushButton("Cancel")
        self.cancel_countdown_button.clicked.connect(self._cancel_countdown)
        self.cancel_countdown_button.setEnabled(False)
        countdown_button_row.addWidget(self.cancel_countdown_button)
        layout.addLayout(countdown_button_row)

        countdown_hint = QLabel("This timer only runs while this window is open.")
        countdown_hint.setProperty("class", "caption")
        countdown_hint.setWordWrap(True)
        layout.addWidget(countdown_hint)

        self._update_ring()

    # --- Focus session (unchanged) ---
    def _format(self, seconds):
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"

    def update_display(self, seconds):
        self.time_label.setText(self._format(seconds))

    def _toggle(self):
        self.main_window.toggle_focus_session()
        is_running = self.main_window.active_focus_session_id is not None
        self.toggle_button.setText("Stop Focus Session" if is_running else "Start Focus Session")

    def _reset(self):
        self.main_window.reset_focus_session()
        self.toggle_button.setText("Start Focus Session")
        self.update_display(0)

    # --- Quick countdown timer ---
    def _update_ring(self):
        fraction = self.countdown_remaining_seconds / self.countdown_total_seconds if self.countdown_total_seconds else 1.0
        self.ring.set_state(fraction, self._format(self.countdown_remaining_seconds))

    def _handle_start_pause_resume(self):
        if not self.countdown_running and not self.countdown_paused:
            self._start_countdown()
        elif self.countdown_running:
            self._pause_countdown()
        elif self.countdown_paused:
            self._resume_countdown()

    def _start_countdown(self):
        minutes = self.minutes_input.value()
        self.countdown_total_seconds = minutes * 60
        self.countdown_remaining_seconds = self.countdown_total_seconds
        self.countdown_running = True
        self.countdown_paused = False
        self.minutes_input.setEnabled(False)
        self.start_countdown_button.setText("Pause")
        self.cancel_countdown_button.setEnabled(True)
        self._update_ring()
        self.countdown_timer.start(1000)

    def _pause_countdown(self):
        self.countdown_timer.stop()
        self.countdown_running = False
        self.countdown_paused = True
        self.start_countdown_button.setText("Resume")

    def _resume_countdown(self):
        self.countdown_running = True
        self.countdown_paused = False
        self.start_countdown_button.setText("Pause")
        self.countdown_timer.start(1000)

    def _countdown_tick(self):
        self.countdown_remaining_seconds -= 1
        self._update_ring()
        if self.countdown_remaining_seconds <= 0:
            self._finish_countdown()

    def _cancel_countdown(self):
        self.countdown_timer.stop()
        self.countdown_running = False
        self.countdown_paused = False
        self.countdown_remaining_seconds = 0
        self.countdown_total_seconds = 0
        self.minutes_input.setEnabled(True)
        self.start_countdown_button.setText("Start Timer")
        self.cancel_countdown_button.setEnabled(False)
        self._update_ring()

    def _finish_countdown(self):
        self.countdown_timer.stop()
        self.countdown_running = False
        self.countdown_paused = False
        self.minutes_input.setEnabled(True)
        self.start_countdown_button.setText("Start Timer")
        self.cancel_countdown_button.setEnabled(False)
        self._fire_completion_notification()

    def _fire_completion_notification(self):
        minutes = self.minutes_input.value()
        message = f"Your {minutes}-minute timer is up!"

        try:
            from plyer import notification as os_notification
            os_notification.notify(title="Timer finished", message=message, timeout=10)
        except Exception:
            pass

        if self.main_window.current_profile:
            from app.data.repository import NotificationLogRepository
            NotificationLogRepository().add(
                self.main_window.current_profile.id, "task", 0, message
            )
            self.main_window.notification_bell.refresh_count()

    def closeEvent(self, event):
        if self.countdown_running:
            self._cancel_countdown()
        event.accept()