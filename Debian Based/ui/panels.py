import os
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
from datetime import datetime


class ControlPanel(ttk.Frame):
    """Top toolbar with global actions."""

    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback

        ttk.Button(self, text="New Scan",
                   command=lambda: callback("new_scan")).pack(side="left", padx=3)
        ttk.Button(self, text="Export Log",
                   command=lambda: callback("export")).pack(side="left", padx=3)
        ttk.Button(self, text="Settings",
                   command=lambda: callback("settings")).pack(side="left", padx=3)
        ttk.Button(self, text="Help",
                   command=lambda: callback("help")).pack(side="right", padx=3)
        ttk.Button(self, text="Quit",
                   command=lambda: callback("quit")).pack(side="right", padx=3)


class ButtonPanel(ttk.Frame):
    """Centered button grid with 15 action buttons."""

    # (label, command) — commands are lists for subprocess, or strings for input prompts
    BUTTON_ACTIONS = [
        ("nemo: File Explorer", ["nemo", "/"]),
        ("Dolphin: File Explorer", ["dolphin", "/"]),
        ("User/Group Configuration", ""),
        ("Linux 3D System: Setup", ["ldps", ""]),
        ("Linux Advanced Security", ["lasui", "", "", ""]),
        ("Safing io: Port Master", ["portmaster"]),
        ("Uncomplicated Firewall", ["gufw", ""]),
        ("Linux Advanced Firewall", ["alfirewall", "", ""]),
        ("Proton Drive Utility App", ["pdua", "", "", ""]),
        ("Proton VPN App", [
         "/usr/bin/flatpak", "run",
         "--branch=stable",
         "--arch=x86_64",
         "--command=protonvpn-app",
         "--file-forwarding",
         "com.protonvpn.www",
         "@@u", "%u", "@@"
        ]),
        ("GUI Clam Anti-Virus", [
         "/usr/bin/flatpak", "run",
         "--branch=stable",
         "--arch=x86_64",
         "--command=clamui",
         "--file-forwarding",
         "io.github.linx_systems.ClamUI",
         "@@u", "%U", "@@"
        ]),
    ]

    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback

        rows = 3
        cols = 5
        idx = 0

        for row in range(rows):
            for col in range(cols):
                if idx < len(self.BUTTON_ACTIONS):
                    label, cmd = self.BUTTON_ACTIONS[idx]

                    ttk.Button(
                        self,
                        text=label,
                        width=18,
                        command=lambda c=cmd: callback(c)
                    ).grid(row=row, column=col, padx=8, pady=8, sticky="ew")

                    idx += 1

        for i in range(cols):
            self.columnconfigure(i, weight=1)

class StatusBar(ttk.Frame):
    """Bottom status bar."""

    def __init__(self, parent):
        super().__init__(parent)
        self.label = ttk.Label(self, text="  Ready.", anchor="w")
        self.label.pack(fill="x")

    def set(self, message):
        self.label.config(text=f"  {message}")
