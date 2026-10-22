"""One Windows console entry, with optional handoff to Windows Terminal."""

import base64
import ctypes
import os
import shutil
import subprocess
import sys


def restore_streams() -> None:
    # Textual's Windows driver writes to __stdout__, not just stdout.
    for name, device, mode in (("stdin", "CONIN$", "r"), ("stdout", "CONOUT$", "w"),
                               ("stderr", "CONOUT$", "w")):
        stream = getattr(sys, name)
        if stream is None:
            stream = open(device, mode, encoding="utf-8", buffering=1)
            setattr(sys, name, stream)
        if getattr(sys, f"__{name}__") is None:
            setattr(sys, f"__{name}__", stream)


def launch() -> bool:
    """Return true to run here; false after handing off to another terminal."""
    if sys.platform != "win32":
        raise RuntimeError("The console launcher is Windows-only")
    arguments = sys.argv[1:]
    try:
        terminal_child = arguments[:1] == ["--terminal-child"]
        if terminal_child:
            arguments = arguments[1:]
            sys.argv[1:] = arguments
        if arguments not in ([], ["--smoke-test"], ["--terminal-smoke-test"]):
            raise ValueError("Unsupported launcher arguments")
        kernel = ctypes.windll.kernel32
        processes = (ctypes.c_ulong * 2)()
        count = kernel.GetConsoleProcessList(processes, len(processes))
        attached = not count and kernel.AttachConsole(-1)
        # shortcut: a sole console process means double-click, revisit for shell-less Windows hosts.
        if terminal_child or count > 1 or attached:
            if not count and not attached and not kernel.AllocConsole():
                raise OSError("Unable to allocate console")
            restore_streams()
            return True
        command = [sys.executable, "--terminal-child", *arguments]
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
                return False
            except (OSError, subprocess.SubprocessError):
                pass
        if not count and not kernel.AllocConsole():
            raise OSError("Unable to allocate console")
        restore_streams()
        return True
    except (OSError, ValueError, subprocess.SubprocessError):
        ctypes.windll.user32.MessageBoxW(None, "无法启动微信视频号下载。请完整解压程序包，或在终端运行 wechat-channels-downloader.exe。",
                                        "微信视频号下载", 0x10)
        raise SystemExit(1)
