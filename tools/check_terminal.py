"""Exercise the real POSIX terminal driver with offline external services."""

from __future__ import annotations

import os
import select
import signal
import subprocess
import sys
import tempfile
import time


def check_terminal(command: list[str]) -> None:
    if sys.platform == "win32":
        raise RuntimeError("This check requires a POSIX terminal")
    import pty
    import termios

    master, slave = pty.openpty()
    before = termios.tcgetattr(slave)
    output = bytearray()
    try:
        with tempfile.TemporaryDirectory() as folder:
            environment = {**os.environ, "TERM": "xterm-256color"}
            with subprocess.Popen([*command, "--terminal-smoke-test"], stdin=slave, stdout=slave,
                                  stderr=slave, cwd=folder, env=environment, start_new_session=True) as process:
                deadline = time.monotonic() + 60
                try:
                    while process.poll() is None:
                        if time.monotonic() >= deadline:
                            raise TimeoutError("Terminal smoke check did not exit")
                        if select.select([master], [], [], 0.1)[0]:
                            output.extend(os.read(master, 65536))
                finally:
                    if process.poll() is None:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
                while select.select([master], [], [], 0)[0]:
                    output.extend(os.read(master, 65536))
                assert process.returncode == 0, f"Terminal smoke exited with code {process.returncode}"
        assert b"\x1b[?1049h" in output, "Check did not enter the real terminal screen"
        assert b"SMOKE_OK" in output, "Offline browser/TUI check did not complete"
        assert b"\x1b[5 q" in output, "Input did not enable the native blinking bar caret"
        assert b"\x1b[0 q" in output, "Exit did not restore the configured cursor shape"
        after = termios.tcgetattr(slave)
        if sys.platform == "darwin":
            # XNU sets PENDIN when restoring canonical input; it is pending-input state, not a setting.
            before[3] &= ~termios.PENDIN
            after[3] &= ~termios.PENDIN
        assert after == before, f"TUI exit changed terminal attributes: before={before!r}, after={after!r}"
    finally:
        os.close(master)
        os.close(slave)
    print("TERMINAL_OK: offline TUI quit restores original terminal attributes.")


if __name__ == "__main__":
    if os.name != "posix":
        raise SystemExit("This check requires a POSIX terminal")
    check_terminal(sys.argv[1:])
