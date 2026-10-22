"""One console entry with opt-in console allocation on supported Windows."""
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, copy_metadata
from playwright.sync_api import sync_playwright

root = Path(SPECPATH).parent
name = "wechat-channels-downloader"
datas, binaries, hiddenimports = [], [], []
for package in ("textual", "playwright"):
    data, binary, hidden = collect_all(package)
    datas += data
    binaries += binary
    hiddenimports += hidden
for package in ("textual", "playwright", "httpx", "pillow"):
    datas += copy_metadata(package, recursive=True)
with sync_playwright() as playwright:
    executable = Path(playwright.chromium.executable_path)
browser = next(path for path in executable.parents if path.name.startswith("chromium-"))
datas.append((str(browser), "browsers/" + browser.name))
datas.append((str(root / "downloader" / "assets"), "downloader/assets"))
a = Analysis([str(root / "main.py")], pathex=[str(root)], binaries=binaries, datas=datas,
             hiddenimports=hiddenimports)
pyz = PYZ(a.pure)
console = EXE(pyz, a.scripts, [], exclude_binaries=True, name=name, console=True,
              manifest=str(root / "tools" / "windows.manifest"),
              icon=str(root / "downloader" / "assets" / "logo.ico"))
COLLECT(console, a.binaries, a.datas, name=name)
