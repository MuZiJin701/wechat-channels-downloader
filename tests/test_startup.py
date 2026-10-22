import base64
import contextlib
import io
import os
import sys
import unittest
from unittest.mock import patch

import main
from downloader.launcher import launch, restore_streams


@unittest.skipUnless(sys.platform == "win32", "Windows console and Windows Terminal entry")
class WindowsStartupTests(unittest.TestCase):
    def test_detached_entry_relaunches_itself_and_prefers_powershell_seven(self):
        with (patch.object(sys, "executable", "D:/归档;tools' test/wechat-channels-downloader.exe"),
              patch.object(sys, "argv", ["program.exe", "--terminal-smoke-test"]),
              patch("ctypes.windll.kernel32.GetConsoleProcessList", return_value=0),
              patch("ctypes.windll.kernel32.AttachConsole", return_value=0),
              patch("shutil.which", side_effect=lambda name: {"wt.exe": "wt.exe", "pwsh.exe": "pwsh.exe"}.get(name)),
              patch("subprocess.run") as started):
            self.assertFalse(launch())
            arguments = started.call_args.args[0]
            self.assertEqual(arguments[:3], ["wt.exe", "-w", "new"])
            self.assertIn("pwsh.exe", arguments)
            command = base64.b64decode(arguments[-1]).decode("utf-16-le")
            self.assertIn("wechat-channels-downloader.exe", command)
            self.assertNotIn("-cli.exe", command)
            self.assertIn("归档;tools'' test", command)
            self.assertIn("--terminal-child", command)
            self.assertIn("--terminal-smoke-test", command)

    def test_existing_console_and_attached_parent_stay_in_place(self):
        for count, attached in ((2, 0), (0, 1)):
            with self.subTest(count=count, attached=attached):
                with (patch.object(sys, "argv", ["program.exe"]),
                      patch("ctypes.windll.kernel32.GetConsoleProcessList", return_value=count),
                      patch("ctypes.windll.kernel32.AttachConsole", return_value=attached),
                      patch("ctypes.windll.kernel32.AllocConsole") as allocated,
                      patch("subprocess.run") as started):
                    self.assertTrue(launch())
                    allocated.assert_not_called()
                    started.assert_not_called()

    def test_legacy_double_click_hands_off_but_terminal_child_does_not_loop(self):
        for child in (False, True):
            with self.subTest(child=child):
                with (patch.object(sys, "argv", ["program.exe", *(["--terminal-child"] if child else [])]),
                      patch("ctypes.windll.kernel32.GetConsoleProcessList", return_value=1),
                      patch("ctypes.windll.kernel32.AttachConsole") as attached,
                      patch("shutil.which", return_value="wt.exe"), patch("subprocess.run") as started):
                    self.assertEqual(launch(), child)
                    self.assertEqual(sys.argv, ["program.exe"])
                    attached.assert_not_called()
                    self.assertEqual(started.call_count, 0 if child else 1)

    def test_terminal_unavailable_or_failed_uses_current_or_allocated_console(self):
        for count in (0, 1):
            for terminal in (None, "wt.exe"):
                with self.subTest(count=count, terminal=terminal):
                    with (patch.object(sys, "argv", ["program.exe"]),
                          patch("ctypes.windll.kernel32.GetConsoleProcessList", return_value=count),
                          patch("ctypes.windll.kernel32.AttachConsole", return_value=0),
                          patch("ctypes.windll.kernel32.AllocConsole", return_value=1) as allocated,
                          patch("shutil.which", return_value=terminal),
                          patch("subprocess.run", side_effect=OSError("private-path")) as started):
                        self.assertTrue(launch())
                        self.assertEqual(allocated.call_count, 0 if count else 1)
                        self.assertEqual(started.call_count, 1 if terminal else 0)

    def test_shell_fallbacks_keep_encoded_or_delayed_arguments(self):
        for powershell in ("powershell.exe", None):
            with self.subTest(powershell=powershell):
                with (patch.dict(os.environ), patch.object(sys, "argv", ["program.exe"]),
                      patch("ctypes.windll.kernel32.GetConsoleProcessList", return_value=0),
                      patch("ctypes.windll.kernel32.AttachConsole", return_value=0),
                      patch("shutil.which", side_effect=lambda name: "wt.exe" if name == "wt.exe" else
                            powershell if name == "powershell.exe" else None), patch("subprocess.run") as started):
                    self.assertFalse(launch())
                    arguments = started.call_args.args[0]
                    self.assertIn(powershell or os.environ["ComSpec"], arguments)
                    if not powershell:
                        self.assertEqual(arguments[-1], "%WCD_LAUNCH_COMMAND%")
                        self.assertIn("--terminal-child", os.environ["WCD_LAUNCH_COMMAND"])

    def test_missing_python_and_textual_streams_are_restored_without_replacing_redirection(self):
        with contextlib.ExitStack() as stack:
            for name in ("stdin", "stdout", "stderr", "__stdin__", "__stdout__", "__stderr__"):
                stack.enter_context(patch.object(sys, name, None))
            streams = [io.StringIO() for _ in range(3)]
            opened = stack.enter_context(patch("builtins.open", side_effect=streams))
            restore_streams()
            self.assertIs(sys.stdin, sys.__stdin__)
            self.assertIs(sys.stdout, sys.__stdout__)
            self.assertIs(sys.stderr, sys.__stderr__)
            self.assertEqual([call.args[0] for call in opened.call_args_list], ["CONIN$", "CONOUT$", "CONOUT$"])
            restore_streams()
            self.assertEqual(opened.call_count, 3)

    def test_startup_failure_has_nonzero_exit_and_does_not_expose_private_paths(self):
        with (patch.object(sys, "argv", ["program.exe"]),
              patch("ctypes.windll.kernel32.GetConsoleProcessList", return_value=0),
              patch("ctypes.windll.kernel32.AttachConsole", return_value=0),
              patch("ctypes.windll.kernel32.AllocConsole", side_effect=OSError("private-path")),
              patch("shutil.which", return_value=None), patch("ctypes.windll.user32.MessageBoxW") as message):
            with self.assertRaises(SystemExit) as error:
                launch()
            self.assertEqual(error.exception.code, 1)
            self.assertNotIn("private-path", message.call_args.args[1])

    def test_source_offline_smoke_does_not_open_a_terminal(self):
        output = io.StringIO()
        with (patch.object(sys, "argv", ["program.exe", "--smoke-test"]),
              patch("subprocess.run") as started, contextlib.redirect_stdout(output)):
            main.main()
        self.assertIn("SMOKE_OK", output.getvalue())
        started.assert_not_called()
