import base64
import contextlib
import io
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import main


@unittest.skipUnless(sys.platform == "win32", "Windows console and Windows Terminal entry")
class WindowsStartupTests(unittest.TestCase):
    def test_double_click_hands_off_to_windows_terminal_without_shell_path_interpretation(self):
        with (patch.dict(os.environ, {"WT_SESSION": ""}),
              patch.object(main, "__file__", "D:/归档;tools' test/main.py"),
              patch.object(sys, "argv", ["main.py", "--smoke-test"]),
              patch.object(sys.stdin, "isatty", return_value=True),
              patch.object(sys.stdout, "isatty", return_value=True),
              patch("ctypes.windll.kernel32.GetConsoleProcessList", return_value=1),
              patch("shutil.which", return_value="C:/WindowsApps/wt.exe"),
              patch("subprocess.run") as launch):
            main.main()
            arguments = launch.call_args.args[0]
            self.assertEqual(arguments[0], "C:/WindowsApps/wt.exe")
            self.assertIn("-EncodedCommand", arguments)
            command = base64.b64decode(arguments[-1]).decode("utf-16-le")
            self.assertIn("--in-terminal", command)
            self.assertIn(str(Path(main.__file__).resolve()).replace("'", "''"), command)
            self.assertIn("--smoke-test", command)

    def test_existing_console_missing_terminal_and_launch_failure_run_offline_tui(self):
        for processes, terminal, failure in ((2, "wt.exe", None), (1, None, None), (1, "wt.exe", OSError("failed"))):
            with self.subTest(processes=processes, terminal=terminal, failure=bool(failure)):
                output = io.StringIO()
                with (patch.dict(os.environ, {"WT_SESSION": ""}),
                      patch.object(sys, "argv", ["main.py", "--smoke-test"]),
                      patch.object(sys.stdin, "isatty", return_value=True),
                      patch("ctypes.windll.kernel32.GetConsoleProcessList", return_value=processes),
                      patch("shutil.which", return_value=terminal),
                      patch("subprocess.run", side_effect=failure),
                      contextlib.redirect_stdout(output)):
                    main.main()
                self.assertIn("SMOKE_OK", output.getvalue())

    def test_hosted_entry_does_not_launch_another_terminal(self):
        output = io.StringIO()
        with (patch.object(sys, "argv", ["main.py", "--in-terminal", "--smoke-test"]),
              patch.object(sys.stdin, "isatty", return_value=True),
              patch("ctypes.windll.kernel32.GetConsoleProcessList", return_value=1),
              patch("subprocess.run") as launch,
              contextlib.redirect_stdout(output)):
            main.main()
        self.assertIn("SMOKE_OK", output.getvalue())
        launch.assert_not_called()
