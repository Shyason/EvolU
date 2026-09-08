from __future__ import annotations

from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QVBoxLayout

from app.data.repository import HabitRepository
from app.ui.habit_heatmap_widget import HabitHeatmapWidget


class HabitHeatmapDialog(QDialog):
    def __init__(self, habit_id: int, parent=None):
        super().__init__(parent)
        self.habit_repo = HabitRepository()
        habit = self.habit_repo.get_by_id(habit_id)  # already eager-loads completions (Step 6)

        self.setWindowTitle(f"{habit.title} — History")

        layout = QVBoxLayout(self)

        stats_row = QHBoxLayout()
        stats_row.addWidget(QLabel(f"<b>Current streak:</b> 🔥 {habit.current_streak}"))
        stats_row.addWidget(QLabel(f"<b>Longest streak:</b> 🏆 {habit.longest_streak}"))
        stats_row.addStretch()
        layout.addLayout(stats_row)

        completed_dates = {c.date for c in habit.completions}
        heatmap = HabitHeatmapWidget(habit, completed_dates)
        layout.addWidget(heatmap)

        legend_row = QHBoxLayout()
        legend_row.addWidget(QLabel("🟩 Completed   🟥 Missed   ⬛ Not scheduled"))
        legend_row.addStretch()
        layout.addLayout(legend_row)