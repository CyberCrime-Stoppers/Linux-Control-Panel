# SereneOS Control Panel (Serene Edition)

A Serene-themed control panel built with **PySide6 (Qt6)** that runs on both:

- **SereneOS** (Arch-family → `pacman` backend)
- **KDE Neon** (Debian-family → `apt` backend)

Distro detection is automatic via `/etc/os-release` — the same UI and the
same code drive whichever machine it lands on. The original Tkinter
launcher (`main.py` / `ui/app.py` / `ui/worker.py`) is untouched.

## Run

```bash
cd Linux-Control-Panel
python3 serene_control_panel.py     # PySide6 required
```

Dependency: `sudo apt install python3-pyside6` (KDE Neon) — or
`pip install --user PySide6`. On SereneOS/Arch: `sudo pacman -S pyside6`.

Privileged actions (package install/remove, systemctl start/stop/restart/
enable) go through **pkexec** — the GUI never handles passwords itself.

## Structure

```
Linux-Control-Panel/
├── serene_control_panel.py     # entry point — this starts the Serene panel
├── serene_core.py              # distro detect + package drivers (no Qt; CLI-testable)
├── SERENE-PANEL-README.md      # this file
├── main.py                     # (existing) Tkinter launcher — untouched
├── ui/
│   ├── serene_theme.py         # Serene palettes (dark + light) → one QSS builder
│   ├── serene_main_window.py   # sidebar + stacked pages + theme toggle + status bar
│   ├── serene_modules.py       # Overview, Packages, Services, Network pages
│   ├── app.py / panels.py / worker.py   # (existing, untouched)
└── scripts/                    # (existing, untouched)
```

## Modules

| Module    | What it does                                                                 |
|-----------|------------------------------------------------------------------------------|
| Overview  | OS, hostname, kernel, uptime, live RAM bar (polls /proc every 2 s)          |
| Packages  | Search / install / remove / refresh index — driver picked per distro         |
| Services  | systemd service list with start / stop / restart / enable (pkexec)            |
| Network   | Interface overview + Tailscale MagicDNS (100.100.100.100) health check       |

## Theming

All colours live in `ui/serene_theme.py` — `PALETTES["dark"]` and
`PALETTES["light"]`, built around the Serene site palette (sage green
`#9db29a` family + purple `#ad5ab4` family). The header button toggles
themes; the choice persists via QSettings to
`~/.config/SereneForge/SereneOS-Control-Panel.conf`.

## Safety conventions (inherited from icond)

- Confirmation dialog before every destructive action
- Non-blocking package ops via QProcess (`--noconfirm` / `-y` +
  `DEBIAN_FRONTEND=noninteractive` so nothing ever hangs waiting on a
  hidden terminal prompt)
- Failures surface in the status bar + dialog — the GUI never crashes on
  backend errors
- Unsupported distros drop the panel to read-only mode with a notice

## Roadmap

- Firewall module (ufw / firewalld / nftables detection)
- Storage module (lsblk view + mounts)
- Users/groups module
- journald viewer
- Flatpak awareness for the Packages module
