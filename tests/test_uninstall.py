"""Tests for bin/oma-top-menu-uninstall. Every path variable points at a temp
directory: without XDG_RUNTIME_DIR the test would delete the live daemon's folder."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "bin" / "oma-top-menu-uninstall"
PID = "com.lefteros.somnius.oma-top-menu"


class UninstallTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.config = self.home / ".config"
        self.state = self.home / "state"
        self.runtime = self.home / "run"
        (self.config / "omarchy").mkdir(parents=True)
        (self.config / "hypr").mkdir(parents=True)
        (self.runtime / "oma-top-menu").mkdir(parents=True)
        (self.state / "omarchy" / "oma-top-menu").mkdir(parents=True)
        self.shell = self.config / "omarchy" / "shell.json"
        self.original = {"bar": {"layout": {
            "left": [{"id": "omarchy.menu"}, {"id": PID, "dividers": True}, "omarchy.workspaces"],
            "right": [{"id": "omarchy.tray"}, {"id": PID}, "omarchy.clock"]}},
            "plugins": [{"id": PID}, {"id": "other.plugin"}]}
        self.shell.write_text(json.dumps(self.original, indent=2))
        self.input = self.config / "hypr" / "input.lua"
        self.input.write_text('hl.config({})\n\n-- oma-top-menu: begin\nhl.config({ input = { follow_mouse = 2 } })\n-- oma-top-menu: end\n')

    def tearDown(self):
        self.tmp.cleanup()

    def run_script(self, *args):
        env = dict(os.environ, HOME=str(self.home), XDG_CONFIG_HOME=str(self.config),
                   XDG_STATE_HOME=str(self.state), XDG_RUNTIME_DIR=str(self.runtime))
        return subprocess.run([sys.executable, str(SCRIPT), *args], env=env, capture_output=True, text=True)

    def ids(self):
        d = json.loads(self.shell.read_text())
        return {s: [e["id"] if isinstance(e, dict) else e for e in l] for s, l in d["bar"]["layout"].items()}

    def test_dry_run_changes_nothing(self):
        before = self.shell.read_text()
        r = self.run_script()
        self.assertEqual(r.returncode, 0)
        self.assertIn("dry run", r.stdout)
        self.assertEqual(self.shell.read_text(), before)
        self.assertTrue((self.runtime / "oma-top-menu").exists())
        self.assertIn("oma-top-menu: begin", self.input.read_text())

    def test_apply_removes_every_entry_with_a_backup_and_keeps_the_rest(self):
        r = self.run_script("--apply")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.ids(), {"left": ["omarchy.menu", "omarchy.workspaces"],
                                      "right": ["omarchy.tray", "omarchy.clock"]})
        d = json.loads(self.shell.read_text())
        self.assertEqual(d["plugins"], [{"id": "other.plugin"}])
        self.assertEqual(len(list((self.config / "omarchy").glob("shell.json.bak-oma-top-menu-*"))), 1)
        self.assertFalse((self.runtime / "oma-top-menu").exists())
        self.assertFalse((self.state / "omarchy" / "oma-top-menu").exists())
        self.assertNotIn("oma-top-menu", self.input.read_text())
        self.assertEqual(self.input.read_text(), "hl.config({})\n")

    def test_broken_json_writes_nothing(self):
        self.shell.write_text("{not json")
        r = self.run_script("--apply")
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(self.shell.read_text(), "{not json")
        self.assertTrue((self.runtime / "oma-top-menu").exists())

    def test_file_mode_is_kept_and_no_temp_file_is_left(self):
        os.chmod(self.shell, 0o600)
        self.run_script("--apply")
        self.assertEqual(self.shell.stat().st_mode & 0o777, 0o600)
        self.assertEqual([p.name for p in self.shell.parent.iterdir() if p.name.endswith(".tmp")], [])

    def test_nothing_to_clean_is_fine(self):
        self.shell.write_text(json.dumps({"bar": {"layout": {"left": ["omarchy.menu"]}}}))
        r = self.run_script("--apply")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(list((self.config / "omarchy").glob("shell.json.bak-*")), [])


if __name__ == "__main__":
    unittest.main()
