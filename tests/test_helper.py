"""Tests for bin/oma-top-menu-hypr-input. Always run against a temp directory."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HELPER = Path(__file__).resolve().parent.parent / "bin" / "oma-top-menu-hypr-input"
SAMPLE = 'hl.config({\n  input = {\n    kb_layout = "us,gr",\n  },\n})\n'


def run(home, *args):
    env = dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(Path(home) / ".config"))
    return subprocess.run([sys.executable, str(HELPER), "follow_mouse", *args],
                          env=env, capture_output=True, text=True)


class HelperTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.file = self.home / ".config" / "hypr" / "input.lua"
        self.file.parent.mkdir(parents=True)
        self.file.write_text(SAMPLE)

    def tearDown(self):
        self.tmp.cleanup()

    def test_add_replace_remove_is_byte_identical(self):
        for value in ("2", "0", "1"):
            self.assertEqual(run(self.home, value).returncode, 0)
        self.assertEqual(self.file.read_text().count("oma-top-menu: begin"), 1)
        self.assertIn("follow_mouse = 1", self.file.read_text())
        self.assertEqual(run(self.home, "--remove").returncode, 0)
        self.assertEqual(self.file.read_text(), SAMPLE)

    def test_no_trailing_newline_file(self):
        self.file.write_text("x = 1")
        self.assertEqual(run(self.home, "2").returncode, 0)
        self.assertTrue(self.file.read_text().startswith("x = 1\n"))

    def test_rejects_bad_values(self):
        for bad in ("4", "-1", "abc", "1; rm -rf /"):
            self.assertNotEqual(run(self.home, bad).returncode, 0)
        self.assertEqual(self.file.read_text(), SAMPLE)

    def test_missing_file_writes_nothing(self):
        self.file.unlink()
        self.assertNotEqual(run(self.home, "2").returncode, 0)
        self.assertFalse(self.file.exists())

    def test_backup_made_and_pruned(self):
        for _ in range(8):
            run(self.home, "2")
        backups = list(self.file.parent.glob("input.lua.bak.*"))
        self.assertEqual(len(backups), 5)


if __name__ == "__main__":
    unittest.main()
