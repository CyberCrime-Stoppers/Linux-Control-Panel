#!/usr/bin/env python3
"""serene_control_panel.py — entry point for the SereneOS Control Panel.

Run from the repo root:
    python3 serene_control_panel.py

Dependencies: PySide6 (pip install PySide6, or system package python3-pyside6).
Existing Tkinter app (main.py → ui/app.py) is untouched — both coexist.
"""

import sys

from PySide6.QtWidgets import QApplication


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SereneOS Control Panel")
    app.setOrganizationName("SereneForge")

    from ui.serene_main_window import MainWindow
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
