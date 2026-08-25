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


class OutputPanel(ttk.Frame):
    """Scrollable text output with threaded command execution."""

    def __init__(self, parent, worker_pool):
        super().__init__(parent)
        self.worker_pool = worker_pool

        self.text = scrolledtext.ScrolledText(
            self,
            wrap="word",
            state="disabled",
            bg="#11111b",
            fg="#c1c7ca",
            insertbackground="#c1c7ca",
            font=("Monospace", 11),
            padx=12,
            pady=12,
        )
        self.text.pack(fill="both", expand=True)

        # Tag styles for severity levels
        self.text.tag_config("info", foreground="#c1c7ca")
        self.text.tag_config("warn", foreground="#c1c7ca")
        self.text.tag_config("error", foreground="#c1c7ca")
        self.text.tag_config("success", foreground="#c1c7ca")
        self.text.tag_config("cmd", foreground="#c1c7ca", font=("Monospace", 11, "bold"))

    def write(self, msg, tag=None):
        """Append text to output panel. Must be called from main thread."""
        ts = datetime.now().strftime("%H:%M:%S")
        self.text.config(state="normal")
        if tag:
            self.text.insert("end", f"[{ts}] {msg}\n", tag)
        else:
            self.text.insert("end", f"[{ts}] {msg}\n")
        self.text.see("end")
        self.text.config(state="disabled")

    def run_command(self, cmd_list, on_done=None):
        """Submit a command to the worker pool."""
        self.write(f"$ {' '.join(cmd_list)}", "cmd")

        def callback(stdout, stderr, returncode):
            if stdout:
                for line in stdout.strip().splitlines():
                    self.after(0, lambda l=line: self.write(l))
            if returncode != 0 and stderr:
                err = stderr.strip()
                self.after(0, lambda s=err: self.write(s, "error"))
            elif returncode == 0:
                self.after(0, lambda: self.write("\u2713 Command completed", "success"))
            if on_done:
                self.after(0, on_done)

        self.worker_pool.submit(cmd_list, callback)

    def clear(self):
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.config(state="disabled")

    def export_log(self):
        """Save current output to a file. Returns True on success."""
        path = filedialog.asksaveasfilename(
            title="Export Log As",
            defaultextension=".log",
            filetypes=[
                ("Log files", "*.log"),
                ("Text files", "*.txt"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return False

        content = self.text.get("1.0", "end-1c")
        try:
            with open(path, "w") as f:
                f.write(content)
            self.write(f"\u2713 Exported to {path}", "success")
            return True
        except IOError as e:
            self.write(f"\u2717 Export failed: {e}", "error")
            return False


class StatusBar(ttk.Frame):
    """Bottom status bar."""

    def __init__(self, parent):
        super().__init__(parent)
        self.label = ttk.Label(self, text="  Ready.", anchor="w")
        self.label.pack(fill="x")

    def set(self, message):
        self.label.config(text=f"  {message}")
