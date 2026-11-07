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


class SanitizeTest(unittest.TestCase):
    def test_markup_shaped_text_is_kept_as_text_but_bounded(self):
        label = '<img src="https://tracker.invalid/x">' + "a" * 10000
        out = bridge.sanitize_text(label)
        self.assertEqual(len(out), bridge.MAX_LABEL)
        self.assertTrue(out.startswith('<img src="https://tracker.invalid/x">'))   # drawn as plain text by the widget

    def test_control_and_override_characters_are_removed(self):
        self.assertEqual(bridge.sanitize_text("A\x00B\x07C\u202eD\u202aE"), "ABCDE")

    def test_scripts_that_need_joiners_and_isolates_survive(self):
        persian = "می\u200cخواهم"
        self.assertEqual(bridge.sanitize_text(persian), persian)
        self.assertEqual(bridge.sanitize_text("\u2068Linux\u2069"), "\u2068Linux\u2069")

    def test_labels_lose_the_accelerator_suffix_and_are_bounded(self):
        self.assertEqual(bridge.clean_menu_label("Open\tCtrl+O"), "Open")
        self.assertEqual(len(bridge.clean_menu_label("x" * 5000)), bridge.MAX_LABEL)
        self.assertEqual(bridge.clean_menu_label(None), "")

    def test_window_title_and_app_name_are_bounded(self):
        b = bridge.SnapshotBuilder({"class": "app", "title": "t" * 5000, "address": "0x1", "pid": 1})
        self.assertEqual(len(b.title), bridge.MAX_TITLE)
        self.assertLessEqual(len(b.app_name), bridge.MAX_TITLE)


class SanitizeIconTest(unittest.TestCase):
    def test_allowed_forms(self):
        for ok in ("firefox", "org.mozilla.firefox", "/usr/share/icons/x.png", "file:///usr/share/x.png", "image://icon/firefox"):
            self.assertEqual(bridge.sanitize_icon(ok), ok)

    def test_everything_else_is_dropped(self):
        for bad in ("https://tracker.invalid/x.png", "http://x/y", "image://other/provider", "relative/path.png",
                    "ft\x00p", "a" * 600, "../../etc/passwd", "name with spaces", ""):
            self.assertEqual(bridge.sanitize_icon(bad), "", bad)

    def test_line_and_paragraph_separators_are_removed(self):
        self.assertEqual(bridge.sanitize_text("a\u2028b\u2029c"), "abc")


class BoundSnapshotTest(unittest.TestCase):
    def test_huge_menus_are_capped_and_sanitized(self):
        items = [{"id": str(i), "label": "<b>" + "x" * 500 + "\x00", "icon": "https://x/y.png", "type": "item"} for i in range(5000)]
        snap = {"appName": "a" * 999, "title": "t", "icon": "javascript:1", "source": "x",
                "menubar": [{"id": "m", "label": "File", "type": "menu", "items": items}] * 100}
        out = bridge.bound_snapshot(snap)
        self.assertLessEqual(len(out["menubar"]), bridge.MAX_TOP_ENTRIES)
        self.assertLessEqual(len(out["menubar"][0]["items"]), bridge.MAX_ITEMS)
        self.assertLessEqual(len(__import__("json").dumps(out)), bridge.MAX_SNAPSHOT_BYTES)
        first = out["menubar"][0]["items"][0]
        self.assertEqual(first["icon"], "")
        self.assertEqual(len(first["label"]), bridge.MAX_LABEL)
        self.assertNotIn("\x00", first["label"])
        self.assertEqual(len(out["appName"]), bridge.MAX_TITLE)
        self.assertEqual(out["icon"], "")

    def test_depth_is_bounded(self):
        node = {"id": "n", "label": "x", "type": "menu", "items": []}
        for _ in range(30):
            node = {"id": "n", "label": "x", "type": "menu", "items": [node]}
        out = bridge.bound_snapshot({"menubar": [node]})
        depth, cur = 0, out["menubar"][0]
        while cur.get("items"):
            cur = cur["items"][0]
            depth += 1
        self.assertLessEqual(depth, bridge.MAX_DEPTH + 1)


class ExecNoShellTest(unittest.TestCase):
    def test_exec_actions_are_argument_lists(self):
        b = bridge.SnapshotBuilder({"class": "app", "title": "t", "address": "0x1", "pid": 1})
        self.assertEqual(b.exec_cmd("firefox --new-window 'a b'"), {"kind": "exec", "argv": ["firefox", "--new-window", "a b"]})
        self.assertEqual(b.exec_cmd("broken 'quote"), {"kind": "exec", "argv": []})

    def test_a_line_that_does_not_parse_runs_nothing(self):
        self.assertEqual(bridge.clean_exec("evil 'unterminated; rm -rf ~"), "")

    def test_execute_action_never_uses_a_shell(self):
        calls = []
        real = bridge.subprocess.Popen
        bridge.subprocess.Popen = lambda *a, **k: calls.append((a, k))
        try:
            self.assertTrue(bridge.execute_action({"kind": "exec", "argv": ["echo", "$(whoami)", "x;y"]}))
            self.assertFalse(bridge.execute_action({"kind": "exec", "command": "rm -rf ~"}))   # the old shell form is refused
            self.assertFalse(bridge.execute_action({"kind": "exec", "argv": []}))
            self.assertFalse(bridge.execute_action({"kind": "exec", "argv": ["ok", 5]}))
        finally:
            bridge.subprocess.Popen = real
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0][0], ["echo", "$(whoami)", "x;y"])
        self.assertNotIn("shell", calls[0][1])


class SnapshotSizeFloorTest(unittest.TestCase):
    def test_a_snapshot_that_stays_too_big_publishes_no_menu(self):
        old = bridge.MAX_SNAPSHOT_BYTES
        bridge.MAX_SNAPSHOT_BYTES = 200
        try:
            snap = {"appName": "a", "title": "t", "icon": "", "menubar": [
                {"id": "m", "label": "File", "type": "menu", "items": [{"id": str(i), "label": "x" * 100, "type": "item"} for i in range(50)]}]}
            self.assertEqual(bridge.bound_snapshot(snap)["menubar"], [])
        finally:
            bridge.MAX_SNAPSHOT_BYTES = old


class LazyMenuTest(unittest.TestCase):
    def test_top_level_entries_without_items_are_tagged_for_a_rebuild(self):
        atspi = {"kind": "atspi", "app": "Floorp", "pid": 1, "index": [0, 1]}
        snap = {"menubar": [
            {"id": "a", "label": "File", "type": "item", "action": dict(atspi)},                      # lazy: no items yet
            {"id": "b", "label": "Tools", "type": "menu", "items": [{"id": "x"}], "action": None},   # already filled
            {"id": "c", "label": "Help", "type": "item", "action": {"kind": "exec", "argv": ["x"]}},  # not AT-SPI
        ]}
        bridge.tag_lazy_entries(snap, "0xabc")
        self.assertEqual(snap["menubar"][0]["action"]["rebuild_window"], "0xabc")
        self.assertIsNone(snap["menubar"][1]["action"])
        self.assertNotIn("rebuild_window", snap["menubar"][2]["action"])

    def test_rebuild_target(self):
        self.assertEqual(bridge.rebuild_target({"kind": "atspi", "rebuild_window": "0x1"}), "0x1")
        self.assertIsNone(bridge.rebuild_target({"kind": "atspi"}))
        self.assertIsNone(bridge.rebuild_target({"kind": "exec", "rebuild_window": "0x1"}))
        self.assertIsNone(bridge.rebuild_target(None))

    def test_handle_requests_returns_the_action_it_ran(self):
        import json, tempfile
        from pathlib import Path as P
        old_req, old_exec = bridge.REQUEST_FILE, bridge.execute_action
        ran = []
        with tempfile.TemporaryDirectory() as tmp:
            bridge.REQUEST_FILE = P(tmp) / "request.json"
            bridge.execute_action = lambda a: ran.append(a) or True
            try:
                action = {"kind": "atspi", "rebuild_window": "0x9"}
                bridge.REQUEST_FILE.write_text(json.dumps({"action": action}))
                self.assertEqual(bridge.handle_requests({}), action)
                self.assertEqual(ran, [action])
                self.assertIsNone(bridge.handle_requests({}))            # request file was consumed
                bridge.REQUEST_FILE.write_text("{not json")
                self.assertIsNone(bridge.handle_requests({}))
            finally:
                bridge.REQUEST_FILE, bridge.execute_action = old_req, old_exec

    def test_a_dirty_window_is_rebuilt_on_the_next_refresh(self):
        saved = (bridge.hypr_json, bridge.active_window, bridge.SnapshotBuilder)
        built = []
        clients = [client("0xa", 1, "floorp", title="A")]
        bridge.hypr_json = lambda args: {"monitors": [mon("DP-1", 1, True)], "workspaces": [{"id": 1, "lastwindow": "0xa"}], "clients": clients}[args[0]]
        bridge.active_window = lambda: dict(clients[0])

        class B:
            def __init__(self, win): pass
            def build(self):
                built.append(1)
                return {"appName": "floorp", "source": "fake", "menubar": []}
        bridge.SnapshotBuilder = B
        try:
            state = bridge.MenuState()
            state.refresh(); state.refresh()
            self.assertEqual(len(built), 1)                  # cached
            state.mark_dirty("0xa"); state.refresh()
            self.assertEqual(len(built), 2)                  # rebuilt once
            state.refresh()
            self.assertEqual(len(built), 2)
        finally:
            bridge.hypr_json, bridge.active_window, bridge.SnapshotBuilder = saved


if __name__ == "__main__":
    unittest.main()
