import os
import sys
from pathlib import Path


def main() -> None:
    if sys.platform == "win32" and getattr(sys, "frozen", False) and sys.argv[1:] != ["--smoke-test"]:
        from downloader.launcher import launch
        if not launch():
            return
    import asyncio
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
