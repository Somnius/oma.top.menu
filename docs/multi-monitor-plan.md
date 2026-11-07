# Multi-monitor menus (draft for review)

Requirement (Lef): every monitor can show a different workspace and different apps, and each monitor's bar must show the menu of ITS window, not one global menu. Also: uninstall must be clean, and every action the plugin takes must be documented separately.

## Verified facts (2026-11-07)
- The shell builds one bar surface per screen (`Variants { model: Quickshell.screens }` in `Bar.qml`), so one widget instance per monitor; the plugin's service and daemon are one per shell.
- Today the daemon follows ONE window: Hyprland's global `activewindow`. On a second monitor the bar would show the same menu as the first.
- `hyprctl monitors -j` gives each monitor's `name`, `focused`, and `activeWorkspace.id`. `hyprctl workspaces -j` gives each workspace's `monitor` and `lastwindow` (address). So the window shown on any monitor can be derived without moving focus: the focused monitor uses `activewindow`, the others use their active workspace's `lastwindow`.
- `hyprctl output create headless` / `output remove <name>` create and remove a virtual output (hyprctl help), so a second monitor can be emulated for a test.
- This machine has one monitor (DP-3).
- Unknown: how a widget learns its own screen name (the bar facade exposes no screen property; candidates `QsWindow.window.screen.name` or `Window.window.screen.name`); whether Quickshell gets a bar on a headless output; how the bar treats a `shell.json` entry whose plugin is gone.

## Design
Daemon (`bin/omarchy-global-menu-bridge`):
1. A pure function `plan_monitors(monitors, workspaces, active)` returns `{monitor name: window address or None}` (focused monitor -> active window, ignoring untitled shell windows; others -> `lastwindow` of their active workspace). Unit-tested with fixtures.
2. On every Hyprland event that can change it (`activewindow`, `focusedmon`, `workspace`, `activeworkspace`, `openwindow`, `closewindow`, `movewindow`, `monitoradded`, `monitorremoved`, `moveworkspace`), re-plan; rebuild a snapshot only for windows whose address changed or whose cached snapshot is older than a few seconds; focused monitor first.
3. Output: one JSON line per change `{"version":2,"focused":"DP-3","monitors":{"DP-3":{snapshot},"HDMI-A-1":{snapshot}}}`; `active.json` keeps the focused monitor's snapshot (compatible with the file fallback). Menu item ids are prefixed with the window address so two monitors never collide.
4. Per-monitor "last real app" for the shell-window rule (Omamail case): a shell popup on one monitor keeps that monitor's previous menu.
Widget: reads its own screen name and shows `monitors[screen]`, falling back to the focused snapshot when the screen is unknown. A monitor with no window on its workspace shows an empty strip.
Panel: shows each monitor's current app in the status line.

## Test plan
- Unit tests for `plan_monitors` (single monitor, two monitors, empty workspace, shell window, special workspace).
- Emulated monitor: create a headless output, put a different app on its workspace, check each bar shows its own menu, move focus between monitors, close the app, remove the output; check no orphan processes and that the bar returns to normal.
- Check the daemon still runs once, and CPU is low with two monitors.

## Results and decisions (2026-11-07)
- Built as designed: `plan_monitors` (pure, 11 tests), `MenuState` (per-window cache, focused monitor built and published first, final publish always), events `activewindow`, `focusedmon`, `workspace`, `moveworkspace`, `activespecial`, `openwindow`, `closewindow`, `movewindow`, monitor add/remove, workspace create/destroy. Each bar finds its monitor with `Hyprland.monitorFor(QsWindow.window.screen)` (the pattern Omarchy's workspace widget uses).
- Virtual monitor test (`hyprctl output create headless`): each bar showed its own window's menu at the same time, also while focus moved; closing a window cleared that monitor's menu; removing the monitor returned to normal; one daemon; idle CPU about 0.6%.
- Bugs found by the test and fixed: no republish when a monitor's window went away; the daemon crashed after my rewrite deleted the lock function (now covered by tests and an undefined-name check); duplicate IPC handler per monitor (moved to the service).
- Review fixes: most specific frame match, a popup keeps a still-valid window, queued follow-mouse apply, cache bound 120 s.
- Open: two windows of one app on two monitors (frame matching only unit-tested with stubs), a menu click on the monitor that does not have focus, a physical second monitor.
