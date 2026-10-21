import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class BuildTests(unittest.TestCase):
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
