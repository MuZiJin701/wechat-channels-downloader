"""Build one platform's portable package, then execute its offline smoke check."""

from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import tarfile
import zipfile
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
NAME = "wechat-channels-downloader"


def main() -> None:
    package = ROOT / "dist" / NAME
    if package.is_symlink() or any(os.path.lexists(package / name) for name in ("data", "downloads")):
        raise SystemExit("拒绝覆盖包含便携数据的输出目录；请先将现有程序及 data/downloads 整体移到其他位置。")
    subprocess.run([sys.executable, "-m", "playwright", "install", "--no-shell", "chromium"], cwd=ROOT, check=True)
    with sync_playwright() as playwright:
        executable = Path(playwright.chromium.executable_path)
    browser = next(path for path in executable.parents if re.fullmatch(r"chromium-\d+", path.name))
    assert executable.is_file(), "Managed Chromium is missing"
    browser_arguments = [] if sys.platform == "darwin" else [
        "--add-data", f"{browser}{os.pathsep}browsers/{browser.name}"]
    subprocess.run([
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--onedir", "--name", NAME,
        "--distpath", str(ROOT / "dist"), "--workpath", str(ROOT / "build" / "pyinstaller"),
        "--specpath", str(ROOT / "build"), "--collect-all", "textual", "--collect-all", "playwright",
        "--recursive-copy-metadata", "textual", "--recursive-copy-metadata", "playwright",
        "--recursive-copy-metadata", "httpx", "--recursive-copy-metadata", "pillow",
        *browser_arguments, str(ROOT / "main.py"),
    ], cwd=ROOT, check=True)
    if sys.platform == "darwin":
        # Preserve Chromium's signed app bundle and framework symlinks without PyInstaller rewriting its binaries.
        shutil.copytree(browser, package / "_internal" / "browsers" / browser.name, symlinks=True)
    for document in ("README.md", "README.en.md"):
        def package_link(match: re.Match[str]) -> str:
            target = match[1]
            if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:|#", target) or target in ("README.md", "README.en.md"):
                return match[0]
            if target == "THIRD_PARTY_NOTICES.md":
                return "](_internal/THIRD_PARTY_NOTICES.md)"
            source = ROOT / target.split("#", 1)[0]
            assert source.exists(), "README link points to a missing source document"
            kind = "tree" if source.is_dir() else "blob"
            return f"](https://github.com/MuZiJin701/{NAME}/{kind}/main/{quote(target, safe='/#')})"

        readme = re.sub(r"\]\(([^)]+)\)", package_link, (ROOT / document).read_text(encoding="utf-8"))
        (package / document).write_text(readme, encoding="utf-8")
    shutil.copy2(ROOT / "THIRD_PARTY_NOTICES.md", package / "_internal" / "THIRD_PARTY_NOTICES.md")
    shutil.copytree(ROOT / "licenses", package / "_internal" / "licenses", dirs_exist_ok=True)
    system = platform.system().lower()
    if system == "darwin":
        launcher = package / f"{NAME}.command"
        launcher.write_text('#!/bin/sh\ncd -- "$(dirname -- "$0")"\nexec ./wechat-channels-downloader\n', encoding="utf-8")
        launcher.chmod(0o755)
    elif system == "linux":
        shell = 'exec "$(dirname "$1")/wechat-channels-downloader"'
        argument = '"' + re.sub(r'(["`$\\])', r'\\\1', shell).replace("\\", "\\\\") + '"'
        launcher = package / f"{NAME}.desktop"
        launcher.write_text(
            "[Desktop Entry]\nType=Application\nName=微信视频号下载\nTerminal=true\n"
            + f"Exec=sh -c {argument} sh %k\n", encoding="utf-8")
        launcher.chmod(0o755)
    binary = package / (NAME + (".exe" if system == "windows" else ""))
    with tempfile.TemporaryDirectory() as working_directory:
        subprocess.run([str(binary), "--smoke-test"], cwd=working_directory, check=True, timeout=120)
        if os.name == "posix":
            subprocess.run([sys.executable, str(ROOT / "tools" / "check_terminal.py"), str(binary)],
                           cwd=working_directory, check=True, timeout=90)
    assert not (package / "data").exists(), "Smoke check must not ship login state"
    assert not (package / "downloads").exists(), "Smoke check must not ship downloaded content"
    assert {path.name for path in package.glob("*.md")} == {"README.md", "README.en.md"}, "Unexpected package documents"
    assert not (package / "docs").exists(), "Development documents must not be distributed"
    assert (package / "_internal" / "licenses").is_dir(), "Third-party licenses are missing"
    machine = platform.machine().lower()
    architecture = "x64" if machine in ("amd64", "x86_64") else "arm64" if machine in ("aarch64", "arm64") else machine
    archive = shutil.make_archive(str(ROOT / "dist" / f"{NAME}-{system}-{architecture}"),
                                  "zip" if system == "windows" else "gztar", ROOT / "dist", NAME)
    if system == "windows":
        with zipfile.ZipFile(archive) as zipped:
            members = zipped.namelist()
    else:
        with tarfile.open(archive) as tarred:
            members = tarred.getnames()
    if any(name == f"{NAME}/{private}" or name.startswith(f"{NAME}/{private}/")
           for name in members for private in ("data", "downloads")):
        Path(archive).unlink()
        raise SystemExit("归档期间发现用户数据，已取消生成压缩包；本地数据保留。")
    print(archive)


if __name__ == "__main__":
    main()
