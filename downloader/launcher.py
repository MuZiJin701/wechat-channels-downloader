"""Windowless Windows entry; the console executable owns the TUI and its data."""

import base64
import ctypes
import os
import shutil
import subprocess
import sys
from pathlib import Path


def launch() -> None:
    if sys.platform != "win32":
        raise RuntimeError("The windowless launcher is Windows-only")
    binary = Path(sys.executable).with_name("wechat-channels-downloader-cli.exe")
    arguments = sys.argv[1:]
    try:
        if arguments not in ([], ["--smoke-test"], ["--terminal-smoke-test"]):
            raise ValueError("Unsupported launcher arguments")
        command = [str(binary), *arguments]
        if ctypes.windll.kernel32.AttachConsole(-1):
            subprocess.run(command, check=True)
            return
        terminal = shutil.which("wt.exe")
        if terminal:
            powershell = shutil.which("pwsh.exe") or shutil.which("powershell.exe")
            if powershell:
                # Encoded arguments keep wt's semicolon parser and the shell away from local paths.
                script = "& " + " ".join("'" + value.replace("'", "''") + "'" for value in command) + "; exit $LASTEXITCODE"
                encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
                shell = [powershell, "-NoLogo", "-NoProfile", "-EncodedCommand", encoded]
            else:
                # Expand the quoted command after wt parses it; delayed expansion stays off for ! in paths.
                os.environ["WCD_LAUNCH_COMMAND"] = subprocess.list2cmdline(command)
                shell = [os.environ.get("ComSpec", "cmd.exe"), "/d", "/v:off", "/c", "%WCD_LAUNCH_COMMAND%"]
            try:
                subprocess.run([terminal, "-w", "new", "--size", "110,40", "new-tab", "--title", "微信视频号下载",
                                "--suppressApplicationTitle", "--", *shell], check=True, timeout=10)
                return
            except (OSError, subprocess.SubprocessError):
                pass
        subprocess.run(command, check=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
    except (OSError, ValueError, subprocess.SubprocessError):
        ctypes.windll.user32.MessageBoxW(None, "无法启动微信视频号下载。请完整解压程序包，或在终端运行 wechat-channels-downloader-cli.exe。",
                                        "微信视频号下载", 0x10)
