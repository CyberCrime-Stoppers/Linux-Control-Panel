"""serene_modules.py — the panel's pages.

Each page is a plain class exposing `.widget` and `.refresh()` so the main
window can host any mix of modules without circular imports.

Pages included (core release):
  OverviewPage   — live system overview: kernel, uptime, RAM bar
  PackagesPage   — search / install / remove / refresh index, via driver
  ServicesPage   — systemd services: start / stop / restart / enable
  NetworkPage    — interfaces, and the Tailscale MagicDNS health check
"""

import os
import subprocess

from PySide6.QtCore import QTimer, QProcess
from PySide6.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMessageBox, QProgressBar, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

import serene_core as core


# ============================================================
# helpers
# ============================================================

def run(argv: list[str], timeout: int = 20) -> tuple[str, str, int]:
    """Capture-mode subprocess helper for quick reads (systemctl, ip...)."""
    try:
        r = subprocess.run(
            argv, capture_output=True, text=True, timeout=timeout, check=False
        )
        return r.stdout, r.stderr, r.returncode
    except FileNotFoundError:
        return "", f"Not installed: {argv[0]}", -1
    except subprocess.TimeoutExpired:
        return "", f"Timed out after {timeout}s", -1


class Page:
    """Minimal contract every module implements."""

    def __init__(self, window):
        self.window = window
        self.widget = QWidget()
        self.root = QVBoxLayout(self.widget)
        self.root.setContentsMargins(16, 14, 16, 14)

    def refresh(self):
        pass


def _fmt_gb(kib: int) -> str:
    return f"{kib / 1024 / 1024:.1f} GB"


# ============================================================
# Overview
# ============================================================

class OverviewPage(Page):
    """Live system overview — polls /proc every 2 s, never blocks the UI."""

    POLL_MS = 2000

    def __init__(self, window):
        super().__init__(window)
        self.root.addWidget(QLabel("<b>System Overview</b>"))

        self.lbl_distro = QLabel("…")
        self.lbl_host = QLabel("…")
        self.lbl_kernel = QLabel("…")
        self.lbl_uptime = QLabel("…")
        self.lbl_mem = QLabel("…")
        for lbl in (self.lbl_distro, self.lbl_host, self.lbl_kernel,
                    self.lbl_uptime, self.lbl_mem):
            self.root.addWidget(lbl)

        self.bar_mem = QProgressBar()
        self.bar_mem.setRange(0, 100)
        self.root.addWidget(self.bar_mem)

        self.root.addStretch(1)

        self.timer = QTimer(self.widget)
        self.timer.timeout.connect(self._poll)
        self.timer.start(self.POLL_MS)
        self.refresh()

    def refresh(self):
        os_name = core.os_release().get("PRETTY_NAME", "Linux")
        host = os.uname().nodename
        kernel = os.uname().release
        with open("/proc/uptime", "r", encoding="utf-8") as fh:
            up_seconds = int(float(fh.read().split()[0]))
        d, rem = divmod(up_seconds, 86400)
        hh, mm = divmod(rem // 60, 60)
        uptime = f"{d}d {hh}h {mm}m"

        with open("/proc/meminfo", "r", encoding="utf-8") as fh:
            mem = {}
            for line in fh:
                if ":" in line:
                    k, _, v = line.partition(":")
                    mem[k] = int(v.split()[0])  # value in kB

        self.lbl_distro.setText(f"OS: {os_name}")
        self.lbl_host.setText(f"Hostname: {host}")
        self.lbl_kernel.setText(f"Kernel: {kernel}")
        self.lbl_uptime.setText(f"Uptime: {uptime}")

        total_kb = mem.get("MemTotal", 0)
        avail_kb = mem.get("MemAvailable", 0)
        used_kb = total_kb - avail_kb
        pct = int(used_kb * 100 // total_kb) if total_kb else 0
        self.bar_mem.setValue(pct)
        self.lbl_mem.setText(
            f"RAM: {_fmt_gb(used_kb)} / {_fmt_gb(total_kb)} used ({pct}%)"
        )

    def _poll(self):
        try:
            self.refresh()
        except OSError:
            pass  # /proc glitch — next tick retries, never crash the GUI


# ============================================================
# Packages
# ============================================================

class PackagesPage(Page):
    """Search / install / remove / update-index through the distro driver.

    Mutations run through QProcess (non-blocking) using the driver's
    pkexec-wrapped command, and confirm first — the icond convention.
    """

    def __init__(self, window):
        super().__init__(window)
        self.root.addWidget(QLabel("<b>Packages</b>"))

        try:
            self.driver = core.get_driver()
        except core.DistroUnsupported as exc:
            self.root.addWidget(QLabel(
                f"This distro is unsupported for package operations: {exc}"
            ))
            self.driver = None
            return

        self.root.addWidget(QLabel(f"Backend: {self.driver.label}"))

        row = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(
            "Search packages… (e.g. dolphin, git, plasma)"
        )
        self.search_box.returnPressed.connect(self.do_search)
        btn_search = QPushButton("🔍 Search")
        btn_search.clicked.connect(self.do_search)
        row.addWidget(self.search_box, stretch=1)
        row.addWidget(btn_search)
        self.root.addLayout(row)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Package", "Installed", "Description"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.root.addWidget(self.table, stretch=1)

        btns = QHBoxLayout()
        b_install = QPushButton("⬇ Install selected")
        b_remove = QPushButton("🗑 Remove selected")
        b_update = QPushButton("🔄 Refresh package index")
        b_install.clicked.connect(self.install_selected)
        b_remove.clicked.connect(self.remove_selected)
        b_update.clicked.connect(self.update_index)
        btns.addWidget(b_install)
        btns.addWidget(b_remove)
        btns.addWidget(b_update)
        btns.addStretch(1)
        self.root.addLayout(btns)

        self.proc = None  # active QProcess, if any
        self.results = []

    def refresh(self):
        pass  # search data loads on demand; nothing expensive runs on tab entry

    # ---------------- actions ----------------

    def do_search(self):
        term = self.search_box.text().strip()
        if not term or self.driver is None:
            return
        self.window.status_msg(f"Searching for '{term}'…")
        try:
            results = self.driver.search(term)
        except core.DriverError as exc:
            self.window.status_msg(f"Search failed: {exc}")
            return

        installed = None
        try:
            installed = self.driver.list_installed()
        except Exception:
            pass  # marked unknown rather than crashing the search results

        self.results = results
        self.table.setRowCount(0)
        for pkg in results:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(pkg["name"]))
            flag = ("Yes" if (installed is not None and pkg["name"] in installed)
                    else ("Yes" if pkg.get("installed") else "—"))
            self.table.setItem(r, 1, QTableWidgetItem(flag))
            self.table.setItem(r, 2, QTableWidgetItem(pkg["desc"][:120]))

        self.window.status_msg(
            f"{len(results)} results for '{term}'"
            + ("" if installed is not None else " (installed-check skipped)")
        )

    def _selected_packages(self) -> list[str]:
        rows = sorted(
            {i.row() for i in self.table.selectedIndexes()}, reverse=True
        )
        names = []
        for r in rows:
            item = self.table.item(r, 0)
            if item is not None:
                names.append(item.text())
        return names

    def _run_pkexec_process(self, argv: list[str]):
        if (self.proc is not None
                and self.proc.state() != QProcess.ProcessState.NotRunning):
            QMessageBox.warning(
                self.widget, "Busy",
                "Another package operation is already running."
            )
            return
        self.proc = QProcess(self.widget)
        self.proc.finished.connect(self._op_done)
        self.window.status_msg(f"Running: {' '.join(argv[1:])}")
        self.proc.start(argv[0], argv[1:])

    def _op_done(self, code: int, status):
        ok = code == 0
        self.window.status_msg(
            "Package operation done ✔" if ok else f"FAILED (exit {code})"
        )
        QMessageBox.information(
            self.widget, "Operation finished",
            "The package operation completed successfully."
            if ok else
            f"The package operation failed (exit code {code}).\n"
            "Check the status bar and try again; pkexec may have been cancelled."
        )
        if ok and self.search_box.text().strip():
            self.do_search()

    def install_selected(self):
        names = self._selected_packages()
        if not names:
            self.window.status_msg("Select a package in the table first.")
            return
        reply = QMessageBox.question(
            self.widget, "Install",
            f"Install {len(names)} package(s)?\n\n{', '.join(names[:10])}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._run_pkexec_process(self.driver.install_cmd(names))

    def remove_selected(self):
        names = self._selected_packages()
        if not names:
            self.window.status_msg("Select a package in the table first.")
            return
        reply = QMessageBox.question(
            self.widget, "Remove",
            f"Remove {len(names)} package(s)?\n\n{', '.join(names[:10])}\n\n"
            "This removes the package and its unneeded dependencies.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._run_pkexec_process(self.driver.remove_cmd(names))

    def update_index(self):
        reply = QMessageBox.question(
            self.widget, "Refresh index",
            "Refresh the package index?\nAn admin password may be requested (pkexec).",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._run_pkexec_process(self.driver.update_cmd())


# ============================================================
# Services
# ============================================================

class ServicesPage(Page):
    """systemd services — shared by both SereneOS (Arch) and KDE Neon."""

    def __init__(self, window):
        super().__init__(window)
        self.root.addWidget(QLabel("<b>Services (systemd)</b>"))

        row = QHBoxLayout()
        b_start = QPushButton("▶ Start")
        b_stop = QPushButton("⏹ Stop")
        b_restart = QPushButton("↻ Restart")
        b_enable = QPushButton("📌 Enable")
        b_refresh = QPushButton("🔄 Refresh")
        for b, fn in (
            (b_start, "start"), (b_stop, "stop"), (b_restart, "restart"),
            (b_enable, "enable"), (b_refresh, "refresh"),
        ):
            b.clicked.connect(lambda _=False, f=fn: self.act(f))
            row.addWidget(b)
        row.addStretch(1)
        self.root.addLayout(row)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Unit", "Active", "Description"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.root.addWidget(self.table, stretch=1)

        self.units = {}
        self.refresh()

    def refresh(self):
        out, err, code = run(
            ["systemctl", "list-units", "--type=service", "--all",
             "--no-pager", "--no-legend"]
        )
        if code != 0:
            self.window.status_msg(f"systemctl failed: {err.strip()[:80]}")
            return
        self.units = {}
        self.table.setRowCount(0)
        for line in out.splitlines():
            parts = line.split()
            if not parts or not parts[0].endswith(".service"):
                continue
            unit, active_state = parts[0], parts[2]
            desc = " ".join(parts[4:]) if len(parts) > 4 else ""
            self.units[unit] = {"state": active_state}
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(unit))
            self.table.setItem(r, 1, QTableWidgetItem(active_state))
            self.table.setItem(r, 2, QTableWidgetItem(desc[:100]))

        self.window.status_msg(f"{self.table.rowCount()} services listed.")

    def _selected_unit(self) -> str | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return item.text() if item else None

    def act(self, action: str):
        if action == "refresh":
            self.refresh()
            return
        unit = self._selected_unit()
        if not unit:
            self.window.status_msg("Select a service first.")
            return
        argv = ["pkexec", "systemctl", action, unit]
        self.window.status_msg(f"Running systemctl {action} {unit}…")
        out, err, code = run(argv, timeout=60)
        if code == 0:
            self.window.status_msg(f"Service '{unit}' {action} done ✔")
            self.refresh()
        else:
            self.window.status_msg(f"Failed: {(err or out).strip()[:80]}")
            QMessageBox.warning(
                self.widget, "Action failed",
                f"systemctl {action} {unit} failed:\n{(err or out)[:300]}"
            )


# ============================================================
# Network
# ============================================================

class NetworkPage(Page):
    """Interfaces overview + Tailscale MagicDNS health check."""

    def __init__(self, window):
        super().__init__(window)
        self.root.addWidget(QLabel("<b>Network</b>"))

        self.root.addWidget(QLabel("Interfaces (ip -br addr):"))
        self.lbl_ifaces = QLabel("…")
        self.lbl_ifaces.setWordWrap(True)
        self.root.addWidget(self.lbl_ifaces)

        self.root.addSpacing(10)
        self.lbl_tailscale = QLabel("…")
        self.lbl_tailscale.setWordWrap(True)
        self.root.addWidget(self.lbl_tailscale)

        self.root.addStretch(1)
        self.refresh()

    def refresh(self):
        out, _, code = run(["ip", "-br", "addr"])
        if code != 0:
            self.lbl_ifaces.setText("(iproute2 not available)")
        else:
            self.lbl_ifaces.setText(out.strip())

        self.lbl_tailscale.setText(
            "Tailscale MagicDNS (100.100.100.100): HEALTHY ✔"
            if self._check_tailscale_dns() else
            "Tailscale MagicDNS (100.100.100.100): unreachable ✘\n"
            "If tailscale0 exists, try: sudo tailscale set --accept-dns=true, "
            "then check resolvectl status tailscale0."
        )

    def _check_tailscale_dns(self) -> bool:
        # Only meaningful if tailscale0 exists; a dig timeout here matches the
        # failure mode debugged on ccs-webserver-a (dig against 100.100.100.100).
        out, _, _ = run(["ip", "link", "show", "tailscale0"])
        if "tailscale0" not in out:
            return False
        _, _, code = run(
            ["dig", "+time=2", "+tries=1", "@100.100.100.100", "ccs-webserver-a."],
            timeout=8,
        )
        return code == 0
