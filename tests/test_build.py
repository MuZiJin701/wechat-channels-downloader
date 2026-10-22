import shutil
import plistlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image
from tools.build import create_launcher


class BuildTests(unittest.TestCase):
    def test_platform_launchers_include_icons_and_keep_the_terminal_entry(self):
        with tempfile.TemporaryDirectory(prefix="图标 ' % ") as directory:
            root = Path(directory)
            for system in ("darwin", "linux"):
                package = root / system
                package.mkdir()
                create_launcher(package, system)
            contents = root / "darwin" / "wechat-channels-downloader.app" / "Contents"
            with (contents / "Info.plist").open("rb") as file:
                info = plistlib.load(file)
            self.assertEqual(info["CFBundleExecutable"], "launch")
            self.assertEqual(info["CFBundlePackageType"], "APPL")
            with Image.open(contents / "Resources" / info["CFBundleIconFile"]) as icon:
                self.assertEqual(icon.size, (1024, 1024))
                icon.verify()
            launcher = (contents / "MacOS" / "launch").read_text(encoding="utf-8")
            self.assertIn('"$contents/Resources/launch.applescript" "$package"', launcher)
            self.assertIn("quoted form of packagePath", (contents / "Resources" / "launch.applescript").read_text())
            desktop = (root / "linux" / "wechat-channels-downloader.desktop").read_text(encoding="utf-8")
            self.assertIn("Icon=" + str((root / "linux").resolve()).replace("\\", "\\\\"), desktop)
            self.assertIn("Terminal=true", desktop)
            self.assertIn(" sh %k", desktop)

    def test_rebuild_refuses_to_overwrite_portable_user_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "tools").mkdir()
            shutil.copy2(Path(__file__).resolve().parents[1] / "tools" / "build.py", root / "tools" / "build.py")
            package = root / "dist" / "wechat-channels-downloader"
            (package / "data").mkdir(parents=True)
            (package / "downloads").mkdir()
            (package / "data" / "session.json").write_bytes(b"preserve-session")
            (package / "downloads" / "video.mp4").write_bytes(b"preserve-download")
            result = subprocess.run([sys.executable, str(root / "tools" / "build.py")],
                                    cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("拒绝覆盖", result.stdout + result.stderr)
            self.assertEqual((package / "data" / "session.json").read_bytes(), b"preserve-session")
            self.assertEqual((package / "downloads" / "video.mp4").read_bytes(), b"preserve-download")
