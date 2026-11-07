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


def client(addr, ws, cls="app", title="T", **kw):
    c = {"address": addr, "class": cls, "title": title, "workspace": {"id": ws}, "mapped": True, "hidden": False}
    c.update(kw)
    return c


def mon(name, ws, focused=False, special=0):
    return {"name": name, "focused": focused, "activeWorkspace": {"id": ws}, "specialWorkspace": {"id": special}}


class PlanMonitorsTest(unittest.TestCase):
    def setUp(self):
        self.clients = [client("0xa", 1, "floorp"), client("0xb", 11, "files"), client("0xc", 11, "dino", focusHistoryID=3)]
        self.workspaces = [{"id": 1, "lastwindow": "0xa"}, {"id": 11, "lastwindow": "0xb"}]

    def test_single_monitor_uses_active_window(self):
        plan = bridge.plan_monitors([mon("DP-1", 1, True)], self.workspaces, self.clients, self.clients[0])
        self.assertEqual(plan["DP-1"]["address"], "0xa")

    def test_two_monitors_each_get_their_own_window(self):
        plan = bridge.plan_monitors([mon("DP-1", 1, True), mon("DP-2", 11)], self.workspaces, self.clients, self.clients[0])
        self.assertEqual(plan["DP-1"]["address"], "0xa")
        self.assertEqual(plan["DP-2"]["address"], "0xb")

    def test_unfocused_monitor_uses_its_last_window_not_the_active_one(self):
        plan = bridge.plan_monitors([mon("DP-1", 1), mon("DP-2", 11, True)], self.workspaces, self.clients, self.clients[1])
        self.assertEqual(plan["DP-1"]["address"], "0xa")
        self.assertEqual(plan["DP-2"]["address"], "0xb")

    def test_empty_workspace_gives_no_window(self):
        plan = bridge.plan_monitors([mon("DP-1", 1, True), mon("DP-2", 21)], self.workspaces, self.clients, self.clients[0])
        self.assertIsNone(plan["DP-2"])

    def test_stale_lastwindow_falls_back_to_a_mapped_window(self):
        ws = [{"id": 1, "lastwindow": "0xa"}, {"id": 11, "lastwindow": "0xgone"}]
        plan = bridge.plan_monitors([mon("DP-1", 1, True), mon("DP-2", 11)], ws, self.clients, self.clients[0])
        self.assertIn(plan["DP-2"]["address"], ("0xb", "0xc"))

    def test_shell_popup_keeps_the_monitors_previous_window(self):
        popup = client("0xp", 1, "org.quickshell", title="")
        prev = {"DP-1": self.clients[0]}
        plan = bridge.plan_monitors([mon("DP-1", 1, True)], self.workspaces, self.clients + [popup], popup, prev)
        self.assertEqual(plan["DP-1"]["address"], "0xa")

    def test_special_workspace_takes_priority(self):
        clients = self.clients + [client("0xs", -99, "scratch")]
        ws = self.workspaces + [{"id": -99, "lastwindow": "0xs"}]
        plan = bridge.plan_monitors([mon("DP-1", 1, False, special=-99)], ws, clients, None)
        self.assertEqual(plan["DP-1"]["address"], "0xs")

    def test_hidden_and_unmapped_windows_are_skipped(self):
        clients = [client("0xh", 1, hidden=True), client("0xm", 1, mapped=False), client("0xok", 1)]
        plan = bridge.plan_monitors([mon("DP-1", 1)], [{"id": 1, "lastwindow": "0xh"}], clients, None)
        self.assertEqual(plan["DP-1"]["address"], "0xok")


class NamespaceTest(unittest.TestCase):
    def test_ids_are_prefixed_recursively(self):
        snap = {"menubar": [{"id": "a.1", "items": [{"id": "a.2"}]}]}
        bridge.namespace_ids(snap, "0xff")
        self.assertEqual(snap["menubar"][0]["id"], "0xff:a.1")
        self.assertEqual(snap["menubar"][0]["items"][0]["id"], "0xff:a.2")


class EventTest(unittest.TestCase):
    def test_relevant_events(self):
        for line in ("activewindowv2>>0xa", "focusedmon>>DP-1,1", "workspacev2>>1,1", "openwindow>>0xa,1,c,t",
                     "monitoradded>>DP-2", "moveworkspacev2>>1,1,DP-2"):
            self.assertTrue(bridge.event_matters(line), line)
        for line in ("windowtitle>>0xa", "urgent>>0xa", "submap>>x"):
            self.assertFalse(bridge.event_matters(line), line)


class LockAndCleanupTest(unittest.TestCase):
    def test_single_instance_lock_is_exclusive_across_processes(self):
        import os
        import subprocess
        import sys
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, XDG_RUNTIME_DIR=tmp)
            code = (
                "import importlib.machinery, importlib.util, sys, time\n"
                "l = importlib.machinery.SourceFileLoader('b', %r)\n"
                "m = importlib.util.module_from_spec(importlib.util.spec_from_loader('b', l)); l.exec_module(m)\n"
                "print(m.acquire_single_instance_lock(), flush=True); time.sleep(float(sys.argv[1]))\n" % str(PATH)
            )
            first = subprocess.Popen([sys.executable, "-c", code, "3"], env=env, stdout=subprocess.PIPE, text=True)
            self.assertEqual(first.stdout.readline().strip(), "True")
            second = subprocess.run([sys.executable, "-c", code, "0"], env=env, capture_output=True, text=True)
            self.assertEqual(second.stdout.strip(), "False")
            first.kill()
            first.wait()

    def test_state_files_are_removed(self):
        import tempfile
        from pathlib import Path as P
        with tempfile.TemporaryDirectory() as tmp:
            old = bridge.STATE_DIR
            bridge.STATE_DIR = P(tmp)
            try:
                (P(tmp) / "active.json").write_text("{}")
                (P(tmp) / "request.json").write_text("{}")
                bridge.remove_state_files()
                self.assertFalse((P(tmp) / "active.json").exists())
                self.assertFalse((P(tmp) / "request.json").exists())
            finally:
                bridge.STATE_DIR = old


class RefreshTest(unittest.TestCase):
    """MenuState.refresh with Hyprland and the snapshot builder faked."""

    def setUp(self):
        self.saved = (bridge.hypr_json, bridge.active_window, bridge.SnapshotBuilder)
        self.clients = [client("0xa", 1, "floorp", title="A"), client("0xb", 11, "files", title="B")]
        self.monitors = [mon("DP-1", 1, True), mon("DP-2", 11)]
        self.workspaces = [{"id": 1, "lastwindow": "0xa"}, {"id": 11, "lastwindow": "0xb"}]

        def fake_json(args):
            return {"monitors": self.monitors, "workspaces": self.workspaces, "clients": self.clients}[args[0]]

        class FakeBuilder:
            def __init__(self, win):
                self.win = win

            def build(self):
                return {"appName": self.win["class"], "source": "fake", "menubar": [{"id": "m.1", "items": []}]}

        bridge.hypr_json = fake_json
        bridge.active_window = lambda: dict(self.clients[0])
        bridge.SnapshotBuilder = FakeBuilder

    def tearDown(self):
        bridge.hypr_json, bridge.active_window, bridge.SnapshotBuilder = self.saved

    def test_each_monitor_gets_its_own_snapshot(self):
        record = bridge.MenuState().refresh()
        self.assertEqual(record["focused"], "DP-1")
        self.assertEqual(record["monitors"]["DP-1"]["appName"], "floorp")
        self.assertEqual(record["monitors"]["DP-2"]["appName"], "files")

    def test_closed_window_clears_that_monitor_and_is_published(self):
        state = bridge.MenuState()
        state.refresh()
        self.clients = [c for c in self.clients if c["address"] != "0xb"]
        self.workspaces = [{"id": 1, "lastwindow": "0xa"}, {"id": 11, "lastwindow": "0x0"}]
        published = []
        state.refresh(publish=lambda r: published.append({k: (v or {}).get("appName") for k, v in r["monitors"].items()}))
        self.assertEqual(published[-1], {"DP-1": "floorp", "DP-2": None})

    def test_ids_are_unique_across_monitors(self):
        record = bridge.MenuState().refresh()
        ids = [snap["menubar"][0]["id"] for snap in record["monitors"].values()]
        self.assertEqual(len(set(ids)), 2)

    def test_removed_monitor_disappears_from_the_record(self):
        state = bridge.MenuState()
        state.refresh()
        self.monitors = [mon("DP-1", 1, True)]
        record = state.refresh()
        self.assertEqual(list(record["monitors"]), ["DP-1"])


class FakeRole:
    def __init__(self, name):
        self.value_name = name


class FakeAcc:
    def __init__(self, role, name="", children=()):
        self._role, self._name, self._children = role, name, list(children)

    def get_role(self):
        return FakeRole(self._role)

    def get_name(self):
        return self._name

    def get_child_count(self):
        return len(self._children)

    def get_child_at_index(self, i):
        return self._children[i]


class FrameMatchTest(unittest.TestCase):
    """Two windows of one application: each monitor must get its own window's menu."""

    def setUp(self):
        self.bar_a = FakeAcc("ATSPI_ROLE_MENU_BAR", "A bar", [FakeAcc("ATSPI_ROLE_MENU", "File")])
        self.bar_b = FakeAcc("ATSPI_ROLE_MENU_BAR", "B bar", [FakeAcc("ATSPI_ROLE_MENU", "File")])
        self.app = FakeAcc("ATSPI_ROLE_APPLICATION", "Floorp", [
            FakeAcc("ATSPI_ROLE_FRAME", "Project Alpha - Floorp", [self.bar_a]),
            FakeAcc("ATSPI_ROLE_FRAME", "Project Beta - Floorp", [self.bar_b]),
        ])

    def extractor(self, title):
        return bridge.AtspiMenuExtractor(1, "Floorp", "0x1", "floorp", title)

    def test_each_window_gets_its_own_menu_bar(self):
        self.assertIs(self.extractor("Project Alpha - Floorp")._frame_menubar(self.app), self.bar_a)
        self.assertIs(self.extractor("Project Beta - Floorp")._frame_menubar(self.app), self.bar_b)

    def test_title_with_extra_text_still_matches_loosely(self):
        self.assertIs(self.extractor("Project Beta - Floorp \u2014 Private")._frame_menubar(self.app), self.bar_b)

    def test_unknown_title_returns_none_so_the_app_wide_search_is_used(self):
        self.assertIsNone(self.extractor("Something else entirely")._frame_menubar(self.app))

    def test_single_window_needs_no_disambiguation(self):
        one = FakeAcc("ATSPI_ROLE_APPLICATION", "Floorp", [FakeAcc("ATSPI_ROLE_FRAME", "Only", [self.bar_a])])
        self.assertIsNone(self.extractor("Only")._frame_menubar(one))


class PlanMonitorsPopupTest(unittest.TestCase):
    def test_popup_does_not_keep_a_window_that_moved_to_another_workspace(self):
        popup = client("0xp", 1, "org.quickshell", title="")
        moved = client("0xa", 7, "floorp")          # was on ws 1, now on ws 7
        other = client("0xz", 1, "dino")
        plan = bridge.plan_monitors([mon("DP-1", 1, True)], [{"id": 1, "lastwindow": "0xp"}],
                                    [popup, moved, other], popup, {"DP-1": client("0xa", 1, "floorp")})
        self.assertEqual(plan["DP-1"]["address"], "0xz")

    def test_unfocused_monitor_keeps_its_last_real_app_when_lastwindow_is_a_popup(self):
        popup = client("0xp", 11, "org.quickshell", title="")
        real = client("0xb", 11, "files")
        spare = client("0xc", 11, "dino", focusHistoryID=1)
        plan = bridge.plan_monitors([mon("DP-1", 1, True), mon("DP-2", 11)],
                                    [{"id": 1, "lastwindow": "0xa"}, {"id": 11, "lastwindow": "0xp"}],
                                    [client("0xa", 1), popup, real, spare], client("0xa", 1), {"DP-2": real})
        self.assertEqual(plan["DP-2"]["address"], "0xb")


class FrameSpecificityTest(unittest.TestCase):
    def test_longest_matching_frame_name_wins(self):
        bar_short = FakeAcc("ATSPI_ROLE_MENU_BAR", "short", [FakeAcc("ATSPI_ROLE_MENU", "File")])
        bar_long = FakeAcc("ATSPI_ROLE_MENU_BAR", "long", [FakeAcc("ATSPI_ROLE_MENU", "File")])
        app = FakeAcc("ATSPI_ROLE_APPLICATION", "App", [
            FakeAcc("ATSPI_ROLE_FRAME", "Notes", [bar_short]),
            FakeAcc("ATSPI_ROLE_FRAME", "Notes for the garden", [bar_long]),
        ])
        ex = bridge.AtspiMenuExtractor(1, "App", "0x1", "app", "Notes for the garden - App")
        self.assertIs(ex._frame_menubar(app), bar_long)


if __name__ == "__main__":
    unittest.main()
