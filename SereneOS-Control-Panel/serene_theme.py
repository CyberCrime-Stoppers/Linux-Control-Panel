"""serene_theme.py — Serene theme tokens and the QSS builder.

One dictionary per palette is the single source of truth for every colour
in the panel (matching the Serene green/purple site palette: sage green
#9db29a family + purple #ad5ab4 family). build_stylesheet() turns a
palette dict into the full application stylesheet — switching themes
swaps exactly one stylesheet and nothing else.

NOTE: flat-layout file — lives NEXT TO serene_control_panel.py so the
whole panel can be copied as loose files in one folder, never needing a
ui/ subpackage.

Format note: the QSS uses %-formatting (not .format/f-strings) because
QSS is brace-heavy and % never collides with braces.
"""

PALETTES = {
    "dark": {
        "window_bg":      "#14161a",
        "sidebar_bg":     "#191c21",
        "card_bg":        "#20242a",
        "border":         "#2c313a",
        "text_primary":   "#e7eaee",
        "text_secondary": "#98a2ad",
        "accent_green":   "#9db29a",   # signature Serene sage — primary actions
        "accent_purple":  "#ad5ab4",   # Serene purple — selection/active indicators
        "accent_hover":   "#b4c8b0",
        "button_text":    "#15181c",
        "success":        "#7fb069",
        "warning":        "#e5a84b",
        "danger":         "#e06c75",
        "hover":          "#272c33",
    },
    "light": {
        "window_bg":      "#f3f5f2",
        "sidebar_bg":     "#e8ece7",
        "card_bg":        "#ffffff",
        "border":         "#d4dbd3",
        "text_primary":   "#1b2420",
        "text_secondary": "#57645c",
        "accent_green":   "#6f8f6a",   # darkened for contrast on light backgrounds
        "accent_purple":  "#8a3f92",
        "accent_hover":   "#5f7d5a",
        "button_text":    "#ffffff",
        "success":        "#4a7c3f",
        "warning":        "#a8720a",
        "danger":         "#b53b46",
        "hover":          "#dde4dc",
    },
}


def build_stylesheet(p: dict) -> str:
    return """
    QWidget { background: %(window_bg)s; color: %(text_primary)s; font-size: 13px; }
    QMainWindow, QDialog { background: %(window_bg)s; }
    QLabel { background: transparent; }

    /* ---------- header ---------- */
    QWidget#header { background: %(sidebar_bg)s; border-bottom: 2px solid %(accent_purple)s; }
    QLabel#header-title { font-size: 20px; font-weight: bold; color: %(accent_green)s; }
    QLabel#header-sub   { font-size: 12px; color: %(text_secondary)s; }

    /* ---------- sidebar ---------- */
    QListWidget#sidebar { background: %(sidebar_bg)s; border: none; outline: none; font-size: 14px; }
    QListWidget#sidebar::item { color: %(text_secondary)s; padding: 10px 14px; margin: 2px 6px; border-radius: 6px; }
    QListWidget#sidebar::item:hover { background: %(hover)s; color: %(text_primary)s; }
    QListWidget#sidebar::item:selected { background: %(accent_purple)s; color: #ffffff; }

    /* ---------- buttons ---------- */
    QPushButton { background: %(accent_green)s; color: %(button_text)s; border: none;
                  border-radius: 6px; padding: 7px 14px; font-weight: bold; }
    QPushButton:hover { background: %(accent_hover)s; }
    QPushButton:disabled { background: %(border)s; color: %(text_secondary)s; }
    QPushButton#toggle { background: %(card_bg)s; color: %(text_primary)s; border: 1px solid %(border)s; }
    QPushButton#danger { background: %(danger)s; color: #ffffff; }

    /* ---------- inputs ---------- */
    QLineEdit, QPlainTextEdit { background: %(card_bg)s; border: 1px solid %(border)s;
                                border-radius: 6px; padding: 6px; color: %(text_primary)s;
                                selection-background-color: %(accent_purple)s; }

    /* ---------- tables ---------- */
    QTableWidget { background: %(card_bg)s; alternate-background-color: %(hover)s;
                   border: 1px solid %(border)s; border-radius: 6px; gridline-color: %(border)s; }
    QHeaderView::section { background: %(sidebar_bg)s; color: %(accent_green)s;
                           border: none; padding: 6px; font-weight: bold; }
    QTableCornerButton::section { background: %(sidebar_bg)s; }

    /* ---------- chrome ---------- */
    QStatusBar { background: %(sidebar_bg)s; color: %(text_secondary)s; }
    QProgressBar { background: %(card_bg)s; border: 1px solid %(border)s; border-radius: 6px;
                   text-align: center; color: %(text_primary)s; }
    QProgressBar::chunk { background: %(accent_purple)s; border-radius: 5px; }
    QScrollBar:vertical { background: %(window_bg)s; width: 10px; }
    QScrollBar::handle:vertical { background: %(border)s; border-radius: 5px; min-height: 30px; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
    """ % p
