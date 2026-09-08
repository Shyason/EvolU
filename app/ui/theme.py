from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtGui import QFontDatabase


@dataclass(frozen=True)
class Palette:
    bg_base: str
    bg_surface: str
    bg_surface_hover: str
    bg_elevated: str
    border: str
    border_focus: str
    text_primary: str
    text_secondary: str
    text_muted: str
    primary: str
    primary_hover: str
    primary_pressed: str
    primary_soft: str
    xp: str
    xp_soft: str
    success: str
    success_soft: str
    danger: str
    danger_soft: str
    warning: str
    warning_soft: str
    card_border: str


EVOLU = Palette(
    bg_base="#0F172A",
    bg_surface="#182338",
    bg_surface_hover="#1F2C45",
    bg_elevated="#182338",
    border="#2A3752",
    border_focus="#3D4E6E",
    text_primary="#F3F4F6",
    text_secondary="#94A3B8",
    text_muted="#64748B",
    primary="#22C55E",
    primary_hover="#16A34A",
    primary_pressed="#15803D",
    primary_soft="#14301F",
    xp="#F59E0B",
    xp_soft="#332008",
    success="#22C55E",
    success_soft="#14301F",
    danger="#FB7185",
    danger_soft="#3A1620",
    warning="#F59E0B",
    warning_soft="#332008",
    card_border="#2A3752",
)

DARK = EVOLU
LIGHT = EVOLU

SPACE_XS, SPACE_SM, SPACE_MD, SPACE_LG, SPACE_XL = 4, 8, 16, 24, 32

RADIUS_SM = "10px"
RADIUS_MD = "18px"
RADIUS_LG = "26px"

TYPE_HEADING = (30, 700)
TYPE_TITLE = (16, 600)
TYPE_BODY = (14, 400)
TYPE_LABEL = (13, 500)
TYPE_CAPTION = (13, 500)

_FONT_FAMILY = "Plus Jakarta Sans"


def load_fonts():
    fonts_dir = Path(__file__).parent / "fonts"
    family_name = _FONT_FAMILY

    for filename in (
        "PlusJakartaSans-Regular.ttf",
        "PlusJakartaSans-Medium.ttf",
        "PlusJakartaSans-SemiBold.ttf",
        "PlusJakartaSans-Bold.ttf",
    ):
        font_path = fonts_dir / filename
        if font_path.exists():
            font_id = QFontDatabase.addApplicationFont(str(font_path))
            if font_id != -1:
                families = QFontDatabase.applicationFontFamilies(font_id)
                if families:
                    family_name = families[0]

    return family_name, family_name


def build_stylesheet(p, heading_font="Plus Jakarta Sans", body_font="Plus Jakarta Sans"):
    return f"""
    * {{
        font-family: "{body_font}";
        color: {p.text_primary};
        outline: none;
    }}

    QWidget {{
        background-color: {p.bg_base};
    }}

    QMainWindow, QDialog {{
        background-color: {p.bg_base};
    }}

    QDialog {{
        background-color: {p.bg_elevated};
        border: 1px solid {p.border};
        border-radius: {RADIUS_LG};
    }}

    QLabel {{
        background: transparent;
        font-size: {TYPE_BODY[0]}px;
    }}
    QLabel[class="heading"] {{
        font-family: "{heading_font}";
        font-size: {TYPE_HEADING[0]}px;
        font-weight: {TYPE_HEADING[1]};
    }}
    QLabel[class="title"] {{
        font-family: "{heading_font}";
        font-size: {TYPE_TITLE[0]}px;
        font-weight: {TYPE_TITLE[1]};
    }}
    QLabel[class="caption"] {{
        font-size: {TYPE_CAPTION[0]}px;
        font-weight: {TYPE_CAPTION[1]};
        color: {p.text_secondary};
    }}

    QPushButton {{
        background-color: {p.bg_surface};
        border: 1.5px solid {p.border};
        border-radius: {RADIUS_SM};
        padding: 10px 20px;
        font-size: {TYPE_BODY[0]}px;
        font-weight: 500;
    }}
    QPushButton:hover {{ background-color: {p.bg_surface_hover}; border-color: {p.border_focus}; }}
    QPushButton:pressed {{ background-color: {p.border}; }}
    QPushButton[class="primary"] {{
        background-color: {p.primary};
        border: none;
        color: #0F172A;
        font-weight: 700;
        padding: 10px 20px;
    }}
    QPushButton[class="primary"]:hover {{ background-color: {p.primary_hover}; color: white; }}
    QPushButton[class="primary"]:pressed {{ background-color: {p.primary_pressed}; color: white; }}

    QLineEdit, QTextEdit, QDateEdit, QTimeEdit, QSpinBox, QComboBox {{
        background-color: {p.bg_surface};
        border: 1.5px solid {p.border};
        border-radius: {RADIUS_SM};
        padding: 9px 12px;
        font-size: {TYPE_BODY[0]}px;
        selection-background-color: {p.primary};
    }}
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{ border: 1.5px solid {p.primary}; }}

    QDateEdit::up-button, QDateEdit::down-button,
    QTimeEdit::up-button, QTimeEdit::down-button,
    QSpinBox::up-button, QSpinBox::down-button {{
        background: transparent;
        border: none;
        width: 18px;
    }}
    QDateEdit::up-arrow, QTimeEdit::up-arrow, QSpinBox::up-arrow {{
        width: 8px; height: 8px;
    }}
    QDateEdit::down-arrow, QTimeEdit::down-arrow, QSpinBox::down-arrow,
    QComboBox::down-arrow {{
        width: 8px; height: 8px;
    }}
    QComboBox::drop-down {{
        border: none;
        width: 26px;
    }}

    QCheckBox::indicator {{
        width: 20px; height: 20px;
        border-radius: 6px;
        border: 1.5px solid {p.border};
        background-color: {p.bg_surface};
    }}
    QCheckBox::indicator:checked {{ background-color: {p.primary}; border-color: {p.primary}; }}

    QTabBar::tab {{
        background: transparent;
        color: {p.text_secondary};
        padding: {SPACE_SM}px {SPACE_LG}px;
        font-weight: 600;
        border-bottom: 3px solid transparent;
    }}
    QTabBar::tab:selected {{ color: {p.primary}; border-bottom: 3px solid {p.primary}; }}

    QScrollBar:vertical {{ background: transparent; width: 10px; }}
    QScrollBar::handle:vertical {{ background: {p.border}; border-radius: 5px; min-height: 30px; }}

        QListWidget#sidebar {{
        background-color: {p.bg_surface};
        border: none;
        border-right: 1px solid {p.border};
        padding: {SPACE_MD}px {SPACE_SM}px;
        outline: none;
    }}
    QListWidget#sidebar::item {{
        color: {p.text_secondary};
        padding: 12px 14px;
        border-radius: {RADIUS_SM};
        margin-bottom: 4px;
        font-weight: 700;
        font-size: {TYPE_BODY[0] * 2}px;
    }}
    QListWidget#sidebar::item:hover {{
        background-color: {p.bg_surface_hover};
        color: {p.text_primary};
    }}
    QListWidget#sidebar::item:selected {{
        background-color: {p.primary_soft};
        color: {p.primary};
        border-left: 3px solid {p.primary};
    }}

    QWidget#card {{
        background-color: {p.bg_surface};
        border: 1px solid {p.card_border};
        border-radius: {RADIUS_MD};
    }}
    QWidget#card:hover {{ border-color: {p.primary}; }}
    """
