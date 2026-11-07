"""Pure-function tests for the bridge. Needs no Hyprland, D-Bus or AT-SPI."""
import importlib.machinery
import importlib.util
import unittest
from pathlib import Path

PATH = Path(__file__).resolve().parent.parent / "bin" / "omarchy-global-menu-bridge"
loader = importlib.machinery.SourceFileLoader("bridge", str(PATH))
spec = importlib.util.spec_from_loader("bridge", loader)
bridge = importlib.util.module_from_spec(spec)
loader.exec_module(bridge)


class ShellWindowTest(unittest.TestCase):
    def test_untitled_shell_window_is_shell_ui(self):
        self.assertTrue(bridge.is_shell_window({"class": "org.quickshell", "title": ""}))
        self.assertTrue(bridge.is_shell_window({"class": "org.quickshell", "title": "Quickshell"}))

    def test_titled_shell_window_is_an_app(self):
        self.assertFalse(bridge.is_shell_window({"class": "org.quickshell", "title": "Omamail"}))

    def test_other_class_is_an_app(self):
        self.assertFalse(bridge.is_shell_window({"class": "floorp", "title": ""}))
        self.assertFalse(bridge.is_shell_window({}))


class NormalizeTest(unittest.TestCase):
    def test_double_separators_collapse(self):
        sep = {"type": "separator"}
        item = {"type": "item", "label": "A"}
        menu = [{"type": "menu", "label": "File", "items": [item, sep, sep, item]}]
        out = bridge.normalize_menus(menu)
        kinds = [i["type"] for i in out[0]["items"]]
        self.assertEqual(kinds.count("separator"), 1)


class NameMatchTest(unittest.TestCase):
    def test_norm_strips_punctuation_and_case(self):
        self.assertEqual(bridge.AtspiMenuExtractor._norm("Kotatogram Desktop!"), "kotatogramdesktop")


class SnapshotNameTest(unittest.TestCase):
    def test_titled_shell_window_uses_title_as_name(self):
        b = bridge.SnapshotBuilder({"class": "org.quickshell", "title": "Omamail", "address": "0x1", "pid": 1})
        self.assertEqual(b.app_name, "Omamail")


if __name__ == "__main__":
    unittest.main()
