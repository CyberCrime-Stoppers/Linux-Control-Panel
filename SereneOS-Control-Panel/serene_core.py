"""serene_core.py — distro detection + package-driver backend.

Deliberately plain Python (no Qt imports) so it stays testable from the
CLI and reusable by scripts. The GUI asks a driver for read-only data
here, and for *mutations* asks for the command argv (via install_cmd /
remove_cmd / update_cmd) and runs it through QProcess itself, so long
operations never block the interface and pkexec handles privilege
separation instead of embedding passwords anywhere.

Supported families:
  arch   → SereneOS and friends   (pacman)
  debian → KDE Neon, Ubuntu       (apt-get / dpkg-query)
"""

import functools
import os
import subprocess


class DistroUnsupported(RuntimeError):
    """Raised when /etc/os-release does not match a supported family."""


class DriverError(RuntimeError):
    """Raised for any fatal backend problem worth surfacing in the GUI."""


def _run(argv: list[str], timeout: int = 30) -> str:
    """Run a command, return stdout; raise DriverError with stderr on failure."""
    try:
        r = subprocess.run(
            argv, capture_output=True, text=True, timeout=timeout, check=False
        )
    except FileNotFoundError as exc:
        raise DriverError(f"Not installed: {argv[0]} ({exc})") from exc
    except subprocess.TimeoutExpired as exc:
        raise DriverError(f"Timed out after {timeout}s: {' '.join(argv)}") from exc
    if r.returncode != 0:
        err = (r.stderr or "").strip() or f"exit code {r.returncode}"
        raise DriverError(err)
    return r.stdout


@functools.lru_cache(maxsize=1)
def os_release() -> dict[str, str]:
    info: dict[str, str] = {}
    path = "/etc/os-release"
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if "=" in line:
                    k, _, v = line.partition("=")
                    info[k.strip()] = v.strip().strip('"')
    return info


def pretty_name() -> str:
    return os_release().get("PRETTY_NAME", "Unknown Linux")


@functools.lru_cache(maxsize=1)
def detect_family() -> str:
    """Return 'arch' or 'debian' by reading /etc/os-release — never hardcoded."""
    blob = (
        os_release().get("ID_LIKE", "")
        + " "
        + os_release().get("ID", "")
    ).lower()
    if "arch" in blob:
        return "arch"
    if "debian" in blob or "ubuntu" in blob:
        # KDE Neon reports ID=neon with ID_LIKE="ubuntu debian" — caught here.
        return "debian"
    raise DistroUnsupported(
        f"Unsupported distro (os-release says: {os_release().get('ID', '?')})"
    )


def get_driver() -> "PackageDriver":
    family = detect_family()
    if family == "arch":
        return ArchDriver()
    return DebianDriver()


class PackageDriver:
    """Abstract base: what both pacman and apt sides must provide."""

    label = "abstract"

    def search(self, term: str) -> list[dict]:
        raise NotImplementedError

    def list_installed(self) -> set[str]:
        raise NotImplementedError

    def install_cmd(self, names: list[str]) -> list[str]:
        raise NotImplementedError

    def remove_cmd(self, names: list[str]) -> list[str]:
        raise NotImplementedError

    def update_cmd(self) -> list[str]:
        raise NotImplementedError


class ArchDriver(PackageDriver):
    """pacman backend for SereneOS / Arch-family."""

    label = "pacman (Arch family)"

    def search(self, term: str) -> list[dict]:
        out = _run(["pacman", "-Ss", term])
        results: list[dict] = []
        current: dict | None = None
        for line in out.splitlines():
            if not line.strip():
                continue
            if not line.startswith((" ", "\t")):
                # Block header: "repo/name version [installed]"
                current = {"name": "", "version": "", "desc": "", "installed": False}
                head = line.split(None, 1)
                full = head[0]
                if "/" in full:
                    current["name"] = full.split("/", 1)[1]
                if len(head) > 1:
                    rest = head[1]
                    if "[installed" in rest:
                        current["installed"] = True
                        rest = rest.split("[installed")[0].strip()
                    current["version"] = rest
                results.append(current)
            elif current is not None:
                desc = line.strip()
                current["desc"] = (
                    desc if not current["desc"] else current["desc"] + " " + desc
                )
        return results

    def list_installed(self) -> set[str]:
        out = _run(["pacman", "-Q"])
        return {line.split()[0] for line in out.splitlines() if line.strip()}

    def install_cmd(self, names: list[str]) -> list[str]:
        # --needed skips already-installed; --noconfirm prevents the GUI hang
        # that a "Proceed? [Y/n]" prompt would cause inside QProcess.
        return ["pkexec", "pacman", "--noconfirm", "--needed", "-S", *names]

    def remove_cmd(self, names: list[str]) -> list[str]:
        return ["pkexec", "pacman", "--noconfirm", "-Rs", *names]

    def update_cmd(self) -> list[str]:
        return ["pkexec", "pacman", "--noconfirm", "-Syu"]


class DebianDriver(PackageDriver):
    """apt-get / dpkg-query backend for KDE Neon / Debian family."""

    label = "apt (Debian family)"

    def search(self, term: str) -> list[dict]:
        out = _run(["apt-cache", "search", term], timeout=60)
        results: list[dict] = []
        for line in out.splitlines():
            if " - " in line:
                name, _, desc = line.partition(" - ")
                results.append(
                    {"name": name.strip(), "version": "", "desc": desc.strip(),
                     "installed": False}
                )
        return results

    def list_installed(self) -> set[str]:
        out = _run(
            # NOTE: plain string, not an f-string — dpkg-query needs these
            # $(...) variables passed through literally.
            ["dpkg-query", "-W", "-f=${Package}\\t${Version}\\t${Status}\\n"],
            timeout=60,
        )
        installed: set[str] = set()
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) == 3 and "install ok installed" in parts[2]:
                installed.add(parts[0])
        return installed

    def install_cmd(self, names: list[str]) -> list[str]:
        # DEBIAN_FRONTEND=noninteractive through `pkexec env` — the standard
        # idiom, because apt would otherwise block the QProcess on a debconf
        # dialog nobody can see from a GUI.
        return [
            "pkexec", "env", "DEBIAN_FRONTEND=noninteractive",
            "apt-get", "-y", "install", *names,
        ]

    def remove_cmd(self, names: list[str]) -> list[str]:
        return [
            "pkexec", "env", "DEBIAN_FRONTEND=noninteractive",
            "apt-get", "-y", "remove", *names,
        ]

    def update_cmd(self) -> list[str]:
        # Refreshes the package index only (apt-get update);
        # full upgrades get their own button later.
        return [
            "pkexec", "env", "DEBIAN_FRONTEND=noninteractive",
            "apt-get", "-y", "update",
        ]
