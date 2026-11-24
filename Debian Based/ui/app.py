import tkinter as tk
from tkinter import ttk, messagebox

from ui.panels import ControlPanel, ButtonPanel, StatusBar
from ui.worker import WorkerPool
import subprocess

class App(tk.Tk):
    """Main application window — wires all panels together."""

    def __init__(self):
        super().__init__()

        # Window setup
        self.title("Linux Control Panel \u2014 v1.0.1")
        self.geometry("1100x750")
        self.minsize(800, 500)
        self.configure(bg="#1e1e2e")

        # Handle window close button
        self.protocol("WM_DELETE_WINDOW", self.quit_app)

        # Create worker pool
        self.worker_pool = WorkerPool(max_workers=4)

        # Apply dark theme
        self._apply_theme()

        # Build UI components
        self._create_toolbar()
        self._create_button_panel()
        self._create_status_bar()

    # =========================================================
    # THEME
    # =========================================================

    def _apply_theme(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        # Frames
        style.configure("TFrame", background="#1e1e2e")
        style.configure("Header.TFrame", background="#11111b")

        # Buttons
        style.configure("TButton",
                        background="#313244",
                        foreground="#cdd6f4",
                        padding=(10, 5))
        style.map("TButton",
                  background=[("active", "#45475a"), ("pressed", "#313244")],
                  foreground=[("active", "#cdd6f4")])

        # Labels
        style.configure("TLabel", background="#1e1e2e", foreground="#cdd6f4")
        style.configure("Header.TLabel",
                        background="#11111b",
                        foreground="#89b4fa",
                        font=("Helvetica", 12, "bold"))

        # Scrollbars
        style.configure("Vertical.TScrollbar",
                        background="#313244",
                        troughcolor="#1e1e2e",
                        arrowcolor="#cdd6f4")
        style.configure("Horizontal.TScrollbar",
                        background="#313244",
                        troughcolor="#1e1e2e",
                        arrowcolor="#cdd6f4")

    # =========================================================
    # UI CONSTRUCTION
    # =========================================================

    def _create_toolbar(self):
        self.toolbar = ControlPanel(self, self.on_toolbar_action)
        self.toolbar.pack(fill="x", padx=10, pady=(10, 5))

    def _create_button_panel(self):
        self.button_panel = ButtonPanel(self, self.on_button_action)
        self.button_panel.pack(fill="x", padx=10, pady=5)

    def _create_status_bar(self):
        self.status = StatusBar(self)
        self.status.pack(fill="x", padx=10, pady=(0, 10))

    # =========================================================
    # ACTION HANDLERS
    # =========================================================

    def on_toolbar_action(self, action):
        """Dispatch toolbar button clicks."""
        if action == "new_scan":
            self.output.clear()
            self.output.write("=== NEW SCAN STARTED ===", "info")
            self.status.set("Ready.")

        elif action == "export":
            if self.output.export_log():
                self.status.set("Log exported.")
            else:
                self.status.set("Export cancelled.")

        elif action == "settings":
            self.output.write("Settings dialog not implemented yet", "warn")
            self.status.set("Ready.")

        elif action == "help":
            self.show_help()

        elif action == "quit":
            self.quit_app()

    def on_button_action(self, cmd):
        """Launch GUI applications from the button panel."""
        if isinstance(cmd, str):
            self.status.set("Input required — not implemented yet.")
            return

        self.status.set(f"Launching: {cmd[0]}...")
        try:
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,  # survives if you close the panel
            )
            self.status.set(f"Launched: {cmd[0]}")
        except FileNotFoundError:
            self.status.set(f"Not installed: {cmd[0]}")
        except PermissionError:
            self.status.set(f"Permission denied: {cmd[0]}")

    # =========================================================
    # DIALOGS
    # =========================================================

    def show_help(self):
        help_text = """
Linux Control Panel v1.0.0 \u2014 Linux Configuration & Security Settings

Buttons:
  \u2022 Nemo                           \u2014 File Explorer from Debian/Cinnomon Based
  \u2022 Dolphin                        \u2014 File Explorer from KDE
  \u2022 User/Group Config              \u2014 Manage Your Users and Groups On your system - Github Page https://github.com/CyberCrime-Stoppers/Linux-3D-Printing-System
  \u2022 Linux 3D System: Setup         \u2014 Current user crontab
  \u2022 System Logs                    \u2014 Last 50 syslog lines
  \u2022 Linux Advanced Security        \u2014 Coming Soon to Linux - Github Page https://github.com/CyberCrime-Stoppers/Linux-Advanced-Security-User-Interface
  \u2022 Safing io: Port Master         \u2014 Safing io: Port Master - Website: https://www.safing.io
  \u2022 Uncomplicated Firewall         \u2014 Uncomplicated Firewall (GUFW)
  \u2022 Linux Advanced Firewall        \u2014 Coming soon to Linux - Github Page https://github.com/CyberCrime-Stoppers/Proton-Drive-Utility-App
  \u2022 Proton Drive Utility App       \u2014 Coming Soon to Linux - Github Page https://github.com/CyberCrime-Stoppers
  \u2022 Proton VPN App                 \u2014 By the Proton AG Services (flatpak based) - https://www.proton.me
  \u2022 GUI Clam Anti-Virus            \u2014 Anti-Virus and Dependencies with (flatpak based) - https://www.virustotal.com

"""
        win = tk.Toplevel(self)
        win.title("Help")
        win.geometry("650x550")
        win.configure(bg="#1e1e2e")
        win.transient(self)
        win.grab_set()

        text = tk.Text(
            win,
            wrap="word",
            bg="#11111b",
            fg="#cdd6f4",
            insertbackground="#cdd6f4",
            font=("Monospace", 11),
            padx=24,
            pady=24,
            relief="flat",
        )
        text.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(win, command=text.yview)
        scrollbar.pack(side="right", fill="y")
        text.config(yscrollcommand=scrollbar.set)

        text.insert("1.0", help_text.strip())
        text.config(state="disabled")

        messagebox.showinfo("Help", help_text.strip())
    def quit_app(self):
        """Clean shutdown \u2014 stops workers and closes window."""
        if messagebox.askokcancel("Quit", "Close Linux Control Panel?"):
            self.worker_pool.shutdown()
            self.destroy()
