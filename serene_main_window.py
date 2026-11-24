"""serene_main_window.py — Serene-themed main window (FLAT LAYOUT: repo root).

Structure
---------
MainWindow
 ├─ Header (top)        : SereneOS Control Panel title + distro name + theme toggle
 ├─ Sidebar (left)      : navigation between modules
 ├─ QStackedWidget      : one page per module (Overview / Packages / Services / Network)
 └─ Status bar          : current action/result feedback (the icond convention)

Theme choice persists via QSettings (org SereneForge / app
SereneOS-Control-Panel → ~/.config/SereneForge/SereneOS-Control-Panel.conf).
"""

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMainWindow,
    QPushButton, QStackedWidget, QVBoxLayout, QWidget,
)

from serene_modules import (
    NetworkPage, OverviewPage, PackagesPage, ServicesPage,
)
from serene_theme import PALETTES, build_stylesheet

import serene_core as core

ORG = "SereneForge"
APP = "SereneOS-Control-Panel"
VERSION = "0.1.1"
NAV = [
    ("Overview", "🖥"),
    ("Packages", "📦"),
    ("Services", "⚙"),
    ("Network", "🌐"),
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"SereneOS Control Panel — v{VERSION}")
        self.resize(1000, 640)
        self.setMinimumSize(760, 480)

        self.settings = QSettings(ORG, APP)
        current = self.settings.value("theme", "dark")
        if current not in PALETTES:
            current = "dark"

        self._build_ui()
        self.apply_theme(current)
        self.update_header()
        self.sidebar.setCurrentRow(0)

    # ---------------- UI construction ----------------

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())
        root.addWidget(self._build_body(), stretch=1)
        self.statusBar().showMessage("Ready.")

    def _build_header(self) -> QWidget:
        header = QWidget(objectName="header")
        h = QHBoxLayout(header)
        h.setContentsMargins(16, 10, 16, 10)

        title_box = QVBoxLayout()
        self.header_title = QLabel("SereneOS Control Panel", objectName="header-title")
        self.header_sub = QLabel("…", objectName="header-sub")
        title_box.addWidget(self.header_title)
        title_box.addWidget(self.header_sub)
        h.addLayout(title_box, stretch=1)

        self.btn_theme = QPushButton("🌙 Dark", objectName="toggle")
        self.btn_theme.setToolTip("Switch between the Serene dark and light palettes.")
        self.btn_theme.clicked.connect(self.toggle_theme)
        h.addWidget(self.btn_theme)

        return header

    def _build_body(self) -> QWidget:
        body = QWidget()
        h = QHBoxLayout(body)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        self.sidebar = QListWidget(objectName="sidebar")
        self.sidebar.setFixedWidth(190)
        for name, icon in NAV:
            QListWidgetItem(f"{icon}  {name}", self.sidebar)
        self.sidebar.currentRowChanged.connect(self._navigate)
        h.addWidget(self.sidebar)

        self.stack = QStackedWidget()

        self.pages = {}
        try:
            for name, cls in (
                ("Overview", OverviewPage),
                ("Packages", PackagesPage),
                ("Services", ServicesPage),
                ("Network", NetworkPage),
            ):
                page = cls(self)
                self.pages[name] = page
                self.stack.addWidget(page.widget)
            self.pages["Overview"].refresh()
        except Exception as exc:  # show backend problems in-window, never crash
            from PySide6.QtWidgets import QLabel as _L
            self.stack.addWidget(_L(f"Module init failed: {exc}"))

        h.addWidget(self.stack, stretch=1)
        return body

    # ---------------- navigation ----------------

    def _navigate(self, row: int):
        if not (0 <= row < len(NAV)):
            return
        self.stack.setCurrentIndex(row)
        page = self.pages.get(NAV[row][0])
        if page is not None:
            page.refresh()

    def status_msg(self, text: str):
        self.statusBar().showMessage(text)

    # ---------------- theme ----------------

    def apply_theme(self, name: str):
        self.theme_name = name
        self.setStyleSheet(build_stylesheet(PALETTES[name]))
        self.btn_theme.setText("☀ Light" if name == "dark" else "🌙 Dark")
        self.settings.setValue("theme", name)

    def toggle_theme(self):
        self.apply_theme("light" if self.theme_name == "dark" else "dark")

    def update_header(self):
        try:
            distro = core.pretty_name()
        except Exception:
            distro = "unsupported distro"
        self.header_sub.setText(f"Distro: {distro}  •  Backend: {self._driver_label()}")

    def _driver_label(self) -> str:
        try:
            return core.get_driver().label
        except Exception:
            return "none (read-only mode)"
