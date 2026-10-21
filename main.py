import asyncio
import os
import sys
from pathlib import Path


def main() -> None:
    hosted = sys.argv[1:2] == ["--in-terminal"]
    if hosted:
        del sys.argv[1]
    if sys.platform == "win32" and not hosted and not os.environ.get("WT_SESSION") and sys.stdin.isatty():
        import base64
        import ctypes
        import shutil
        import subprocess

        processes = (ctypes.c_ulong * 2)()
        if ctypes.windll.kernel32.GetConsoleProcessList(processes, len(processes)) == 1:
            terminal = shutil.which("wt.exe")
            if terminal:
                arguments = [sys.executable]
                if not getattr(sys, "frozen", False):
                    arguments.append(str(Path(__file__).resolve()))
                arguments.extend(["--in-terminal", *sys.argv[1:]])
                # wt parses semicolons even inside paths; encoded arguments keep paths literal.
                command = "& " + " ".join("'" + value.replace("'", "''") + "'" for value in arguments) + "; exit $LASTEXITCODE"
                encoded = base64.b64encode(command.encode("utf-16-le")).decode("ascii")
                powershell = Path(os.environ["SystemRoot"]) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
                try:
                    subprocess.run([terminal, "new-tab", "--", str(powershell), "-NoLogo", "-NoProfile",
                                    "-EncodedCommand", encoded], check=True, timeout=10)
                    return
                except (OSError, subprocess.SubprocessError):
                    pass
    if getattr(sys, "frozen", False):
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(Path(__file__).resolve().parent / "browsers")
    terminal = None
    if sys.platform != "win32" and sys.stdin.isatty():
        import termios
        descriptor = sys.stdin.fileno()
        terminal = descriptor, termios.tcgetattr(descriptor)
    try:
        if sys.argv[1:] in (["--smoke-test"], ["--terminal-smoke-test"]):
            from downloader.smoke import smoke
            asyncio.run(smoke(terminal=sys.argv[1] == "--terminal-smoke-test"))
            print("SMOKE_OK: bundled Chromium and TUI; offline temporary session only.")
        else:
            from downloader.app import main as run
            run()
    finally:
        if sys.platform != "win32" and terminal is not None:
            # Node exits after Textual restores the terminal and can overwrite that restoration.
            try:
                termios.tcsetattr(terminal[0], termios.TCSANOW, terminal[1])
            except termios.error:
                pass  # The SSH terminal may already have disconnected.


if __name__ == "__main__":
    main()
