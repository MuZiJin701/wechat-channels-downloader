import os
import sys
import unittest
from pathlib import Path

from tools.check_terminal import check_terminal


@unittest.skipUnless(os.name == "posix", "POSIX PTY check; Windows uses a different console driver")
class TerminalTests(unittest.TestCase):
    def test_real_tui_exit_restores_terminal_after_playwright_driver_stops(self):
        check_terminal([sys.executable, str(Path(__file__).resolve().parents[1] / "main.py")])
