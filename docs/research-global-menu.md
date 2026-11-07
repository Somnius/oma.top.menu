# Global menu on the Omarchy top bar: research (2026-11-07)

Research only. No code or config was changed, and nothing was installed.

## Goal
Like the GNOME "Global Menu" extension (OMG! Ubuntu, 2026-11): the focused app's menus (File/Edit/View...) on the LEFT of the top bar, workspace numbers moved to the RIGHT.

## How the GNOME extension works (article, read in full)
- Default: it builds menus from per-app keyboard-shortcut profiles (about 292 bundled, user-extendable). It works for any toolkit.
- Optional companion daemon: sends the app's real, full menu through (GIMP, Shotwell cited). Repo: Unmade760/orbit-global-menu (GPL-3.0).
- Unknown: the companion's extraction protocol (not in the article; needs its source).

## Catalog (plugins.omarchy.org/catalog.json, 6380 plugins)
The page loads `catalog.json` (about 16 MB) via `assets/js/app.js`. I filtered it for bar widgets, panels and suites that mention menu, workspace or active-window, which left 425 candidates.

JEV (jev-1.14.0) scored each one with 3 Noul questions: `app_menu`, `ws_numbers`, `active_title`. That was 425 requests, about 450 input tokens each, sending only public catalog text. No errors.

app_menu above 0.3:

| plugin | app_menu | ws_numbers | active_title | status |
|---|---|---|---|---|
| primo.global-menu | 0.90 | 0.07 | 0.69 | Manual setup, verified |
| foamy.tray | 0.81 | 0.16 | 0.40 | Available, unverified |
| tsouth89.omcp | 0.31 | 0.31 | 0.57 | Available, unverified |

- foamy.tray is probably a false positive: its description is "system tray with native app menus", which means tray-icon menus. Not confirmed from its source.
- omcp is an MCP server per a first read. Not confirmed from its source.
- Only murdi.named-workspaces scores high on both ws_numbers (0.96) and active_title (0.94). Nothing else combines them.
- 78 plugins score ws_numbers above 0.7, but moving workspaces needs no plugin (see below).
- Verdict: primo.global-menu is the only real candidate.

## primo.global-menu (v1.1.0, maintainer-reviewed 2026-11-03; the catalog and manifest say MIT but the repo's LICENSE is GPL-2.0)
- A bar widget plus a Python daemon (`omarchy-global-menu-bridge`). The daemon extracts the focused app's menu via `org.gtk.Menus`, then dbusmenu, then AT-SPI, then a `.desktop` fallback. It writes `~/.local/state/omarchy/global-menu/active.json`, which the widget renders.
- Terminals and browsers only get the generic fallback menu (README.md:105-106). Ghostty is not installed here, so what it exports is unverified.
- The catalog has no one-click install (`installAvailable:false`). It needs a manual clone plus a systemd user unit.

### Why it failed to load (evidence from `journalctl --user`, 2026-11-07)
- 11:03:35: the daemon crashed at startup with `ModuleNotFoundError: No module named 'gi'` (bridge line 311, via `force_a11y_enabled`). The shebang is `#!/usr/bin/env python3`. A `which -a python3` in my shell lists /usr/bin/python3 first, then mise's python. Which interpreter the `systemd-run` unit used is not verified. System `/usr/bin/python3` has `gi` and Atspi 2.0 (I checked).
- 11:04:00: started again via `/usr/bin/python3`. It ran about 56 s with no error logged, then was stopped. Whether the menu actually rendered then is unknown.
- 11:01:34: quickshell warning "Module path ... is outside of the config folder". Whether that affected loading is unknown.
- The plugin is no longer installed (the plugin directory is gone).
- Not a cause: the manifest is valid (checked against Omarchy's PluginRegistry.qml).

### Concerns
- It forces AT-SPI always on for every app (listener re-registered every 5 s, bridge:2070). The CPU and memory cost is unmeasured.
- The daemon wakes about 20 times a second even when idle (50 ms select, bridge:2089). Menu extraction itself only runs on focus change.
- A request file can hold `{"action":{"kind":"exec","command":...}}`, which the daemon runs with `sh -c` (bridge:1923, 1787). The file is mode 0600, so this is the same trust level as the user. Still worth knowing.

## Workspaces to the right: no plugin needed
The built-in `omarchy.workspaces` entry is currently in `bar.layout.left` of `~/.config/omarchy/shell.json`, right after `omarchy.menu`. The proposed change below is NOT applied:

```diff
 "left":  [ {"id":"omarchy.menu"},
-           {"id":"omarchy.workspaces"} ],
+           {"id":"primo.global-menu"} ],
 "right": [ {"id":"omarchy.tray"}, ...
+           {"id":"omarchy.workspaces"},
```
Where it goes inside `right` is a choice for Lef.

## Recommendation
1. First test primo.global-menu again, running the daemon with the system Python (the failure was a missing `gi` module). Read the quickshell log and `active.json`. About an hour, low risk. Estimate, not measured.
2. If it works but terminals/Electron apps only show the fallback, the useful gap is a shortcut-profile fallback like the GNOME extension's. `Oma Top Menu` (`oma.top.menu`) could then be a fork of primo plus that layer, not a rewrite. The daemon's extraction cascade is the hard part (about 2.2k lines), so a from-scratch build would be days of work. Orbit's profiles are GPL-3.0, so reuse needs a license check, and I haven't looked at their format.
3. Build new only if primo fails a real test for a reason that can't be fixed.

## Unknowns
- Whether primo renders menus on this machine (not tested).
- Ghostty's menu exports (not installed).
- The real CPU cost of AT-SPI always-on.
- Whether foamy.tray and omcp are what JEV says (sources not read).
