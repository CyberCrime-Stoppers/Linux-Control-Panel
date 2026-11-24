#!/usr/bin/env python3
"""serene_control_panel.py — entry point for the SereneOS Control Panel.

Run from wherever these files live (they must sit TOGETHER in one folder):
    python3 serene_control_panel.py

FLAT LAYOUT: every panel file is in the same folder as this script —
serene_core.py, serene_theme.py, serene_main_window.py, serene_modules.py.
No subfolders, no package imports — copy the folder anywhere and it runs.
Imports are sys.path-fixed relative to THIS file, so it works even when
launched from a different working directory.

Dependencies: PySide6 (python3-pyside6 on KDE Neon, pyside6 on Arch).
The original Tkinter launcher (main.py → ui/app.py) remains untouched and
still runs independently.
"""

import os
import sys

# Make imports work no matter where the CWD is: add THIS file's folder
# to sys.path so serene_core / serene_theme / etc. resolve next to it.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    app.setApplicationName("SereneOS Control Panel")
    app.setOrganizationName("SereneForge")

    from serene_main_window import MainWindow
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
