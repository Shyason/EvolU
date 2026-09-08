import sys

from PySide6.QtWidgets import QApplication

from app.data.database import init_db
from app.ui.main_window import MainWindow
from app.ui.theme import load_fonts


def main():
    init_db()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    heading_font, body_font = load_fonts()
    window = MainWindow()
    window._heading_font = heading_font
    window._body_font = body_font
    window._apply_theme()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
