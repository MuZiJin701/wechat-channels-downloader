import base64
import contextlib
import io
import os
import sys
import unittest
from unittest.mock import patch

import main


@unittest.skipUnless(sys.platform == "win32", "Windows console and Windows Terminal entry")
class WindowsStartupTests(unittest.TestCase):
    def test_windowless_entry_uses_new_terminal_and_prefers_powershell_seven(self):
        with (patch.dict(os.environ, {"WT_SESSION": ""}),
              patch.object(sys, "frozen", True, create=True),
              patch.object(sys, "executable", "D:/归档;tools' test/wechat-channels-downloader.exe"),
              patch.object(sys, "argv", ["program.exe", "--smoke-test"]),
              patch.object(sys, "stdin", None),
              patch("ctypes.windll.kernel32.AttachConsole", return_value=0),
              patch("shutil.which", side_effect=lambda name: {"wt.exe": "C:/WindowsApps/wt.exe", "pwsh.exe": "C:/pwsh.exe"}.get(name)),
              patch("subprocess.run") as launch):
            main.main()
            arguments = launch.call_args.args[0]
            self.assertEqual(arguments[0], "C:/WindowsApps/wt.exe")
            self.assertEqual(arguments[1:3], ["-w", "new"])
            self.assertIn("C:/pwsh.exe", arguments)
            self.assertIn("-EncodedCommand", arguments)
            command = base64.b64decode(arguments[-1]).decode("utf-16-le")
            self.assertIn("wechat-channels-downloader-cli.exe", command)
            self.assertIn("归档;tools'' test", command)
            self.assertIn("--smoke-test", command)

    def test_windowless_entry_reuses_parent_console_or_falls_back_when_terminal_unavailable(self):
        for parent, terminal, failure in ((1, "wt.exe", False), (0, None, False), (0, "wt.exe", True)):
            with self.subTest(parent=parent, terminal=terminal, failure=failure):
                with (patch.object(sys, "frozen", True, create=True),
                      patch.object(sys, "stdin", None),
                      patch.object(sys, "argv", ["program.exe"]),
                      patch("ctypes.windll.kernel32.AttachConsole", return_value=parent),
                      patch("shutil.which", side_effect=lambda name: terminal if name == "wt.exe" else "powershell.exe"),
                      patch("subprocess.run", side_effect=[OSError("private-path"), None] if failure else None) as launch):
                    main.main()
                    self.assertTrue(launch.call_args.args[0][0].endswith("-cli.exe"))

    def test_console_entry_does_not_launch_another_terminal(self):
        output = io.StringIO()
        with (patch.object(sys, "argv", ["main.py", "--smoke-test"]),
              patch.object(sys.stdin, "isatty", return_value=True),
              patch("ctypes.windll.kernel32.GetConsoleProcessList", return_value=1),
              patch("subprocess.run") as launch,
              contextlib.redirect_stdout(output)):
            main.main()
        self.assertIn("SMOKE_OK", output.getvalue())
        launch.assert_not_called()

    def test_shell_fallback_and_startup_errors_do_not_expose_private_paths(self):
        for powershell in ("powershell.exe", None):
            with self.subTest(powershell=powershell):
                with (patch.dict(os.environ), patch.object(sys, "frozen", True, create=True),
                      patch.object(sys, "stdin", None), patch.object(sys, "argv", ["program.exe"]),
                      patch("ctypes.windll.kernel32.AttachConsole", return_value=0),
                      patch("shutil.which", side_effect=lambda name: "wt.exe" if name == "wt.exe" else
                            powershell if name == "powershell.exe" else None),
                      patch("subprocess.run") as launch):
                    main.main()
                    arguments = launch.call_args.args[0]
                    self.assertIn(powershell or os.environ["ComSpec"], arguments)
                    if not powershell:
                        self.assertEqual(arguments[-1], "%WCD_LAUNCH_COMMAND%")
                        self.assertIn("-cli.exe", os.environ["WCD_LAUNCH_COMMAND"])
        with (patch.object(sys, "frozen", True, create=True), patch.object(sys, "stdin", None),
              patch.object(sys, "argv", ["program.exe"]),
              patch("ctypes.windll.kernel32.AttachConsole", return_value=0),
              patch("shutil.which", return_value=None), patch("subprocess.run", side_effect=OSError("private-path")),
              patch("ctypes.windll.user32.MessageBoxW") as message):
            main.main()
            self.assertNotIn("private-path", message.call_args.args[1])
