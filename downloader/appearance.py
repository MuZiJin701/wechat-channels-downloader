"""Portable appearance preferences and the two green terminal palettes."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from textual.theme import Theme

THEMES = (
    Theme(name="channels-light", primary="#285633", accent="#164b2b", secondary="#34533a",
          foreground="#0c0d0e", background="#88a28c", surface="#a8bfae", panel="#77977d",
          success="#164d28", warning="#583500", error="#7d1731", dark=False, text_alpha=1,
          variables={"muted": "#2d4934", "entry-bg": "#cbdccf", "line": "#55775c",
                     "button-fg": "#ffffff", "gradient-start": "#285633", "gradient-end": "#b6f0cb"}),
    Theme(name="channels-dark", primary="#8ce5a8", accent="#b6f0cb", secondary="#afc9b5",
          foreground="#dee0e3", background="#283e2c", surface="#1c3021", panel="#35543c",
          success="#afedba", warning="#ffd38a", error="#ffadc0", dark=True, text_alpha=1,
          variables={"muted": "#afc9b5", "entry-bg": "#192e20", "line": "#608069",
                     "button-fg": "#142b1b", "gradient-start": "#4cc06b", "gradient-end": "#b6f0cb"}),
)
MODES = ("system", "light", "dark")


def system_dark() -> bool:
    """Read the executing machine's appearance; unavailable preferences mean light."""
    try:
        if sys.platform == "win32":
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as key:
                value = winreg.QueryValueEx(key, "AppsUseLightTheme")[0]
                return isinstance(value, int) and value == 0
        command = (["defaults", "read", "-g", "AppleInterfaceStyle"] if sys.platform == "darwin" else
                   ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"])
        result = subprocess.run(command, capture_output=True, text=True, timeout=1)
        return result.returncode == 0 and result.stdout.strip().strip("'").lower() in ("dark", "prefer-dark")
    except (OSError, subprocess.SubprocessError):
        return False


def load_mode(root: Path) -> str:
    try:
        settings = json.loads((root / "data" / "appearance.json").read_text(encoding="utf-8"))
        mode = settings.get("theme") if isinstance(settings, dict) else None
        return mode if isinstance(mode, str) and mode in MODES else "system"
    except (OSError, ValueError):
        return "system"


def save_mode(root: Path, mode: str) -> None:
    if mode not in MODES:
        raise ValueError("Unknown appearance mode")
    folder = root / "data"
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=folder, delete=False) as file:
            temporary = Path(file.name)
            json.dump({"theme": mode}, file)
            file.flush()
        temporary.replace(folder / "appearance.json")
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def refresh_desktop_icon(root: Path) -> None:
    launcher = root / "wechat-channels-downloader.desktop"
    if not launcher.is_file() or launcher.is_symlink():
        return
    icon = str(Path(__file__).with_name("assets").resolve() / "logo.png")
    icon = icon.replace("\\", "\\\\").replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
    original = launcher.read_text(encoding="utf-8")
    lines = original.splitlines()
    if "[Desktop Entry]" not in lines:
        return
    start = lines.index("[Desktop Entry]") + 1
    end = next((i for i in range(start, len(lines)) if lines[i].startswith("[")), len(lines))
    index = next((i for i in range(start, end) if lines[i].startswith("Icon=")), end)
    if index < end:
        if lines[index] == f"Icon={icon}":
            return
        lines[index] = f"Icon={icon}"
    else:
        lines.insert(index, f"Icon={icon}")
    updated = "\n".join(lines) + "\n"
    # Desktop Entry requires absolute icon paths; refresh only our portable launcher after a move.
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=root, delete=False) as file:
            temporary = Path(file.name)
            file.write(updated)
        temporary.chmod(launcher.stat().st_mode)
        temporary.replace(launcher)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
