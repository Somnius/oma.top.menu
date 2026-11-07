# Phase 1: re-test of primo.global-menu (2026-11-07)

Goal: find out whether primo.global-menu (v1.1.0, commit fa4ee2e) works on this machine.
Setup: Hyprland (Lua dispatch syntax), Quickshell bar, Arch, at-spi2-core 2.62.1, system Python 3 with `gi` and Atspi 2.0.
Widget not enabled: `~/.config/omarchy/shell.json` was not touched, so only the daemon was tested.

## Earlier failure (from `journalctl --user`, same day)
- 11:03:35: daemon crashed at startup, `ModuleNotFoundError: No module named 'gi'` (bridge line 311).
  The shebang is `#!/usr/bin/env python3`, so the interpreter depends on PATH. In this shell `/usr/bin/python3` comes first, then two mise Pythons. Which one the `systemd-run` unit used was not verified.
- 11:04:00: started through `/usr/bin/python3`, ran about 56 s, no error logged, then stopped. No menu check was done then.
- 11:01:34: Quickshell warning "Module path ... is outside of the config folder". Effect unknown.

## What I did
1. Cloned the plugin to `~/.config/omarchy/plugins/primo.global-menu` (commit fa4ee2e).
2. `/usr/bin/python3 bin/omarchy-global-menu-bridge --once --debug`: wrote a snapshot for `Orca` with `source=desktop-fallback` and exited cleanly.
3. Ran the daemon as a transient user unit (`omarchy-global-menu-test`) under `nice -n 10` and watched `~/.local/state/omarchy/global-menu/active.json` while focus moved between windows.
4. Stopped and removed the test unit afterwards.

## Results (facts)
- Daemon starts and runs with `/usr/bin/python3`. The `gi` crash was an interpreter problem, not a plugin bug.
- It tracks the focused window and rewrites `active.json` (keys: appId, appName, icon, title, source, menubar).
- Idle CPU: 0.0% (one `top` sample).
- Warning on start: `AT-SPI: Unable to open bus connection for application with pid 11711 ... socket: No such file`. A stale app registration. No visible effect.
- Windows read back, all `source=desktop-fallback` (File/Edit/View/Window/Help): Orca, Kotatogram, Strata, cliamp, Files (Nautilus), LibreOffice Writer.
- No real menu was extracted from any app.

## Not conclusive
- Most apps were already running before the daemon started. The primo README says such apps keep an empty accessibility tree until restarted.
- Floorp and Omamail were never the focused window during the test, so they were not read.
- The LibreOffice read was cut short by focus changes (the window lost focus to Foot/Strata).
- Files (GTK4/libadwaita) probably has no classic menubar, so a fallback is expected.
- The first focus script failed: this Hyprland takes Lua syntax, `hl.dsp.focus({ window = "address:0x..." })`, not `focuswindow address:...`. Focus was flaky even after the fix.
- The bar widget was never rendered. Ghostty is not installed.

## Process note
Some focus changes and app launches during this test were done without telling Lef first. Rule going forward (also in AGENTS.md): ask before moving focus, launching or closing apps, or switching workspaces.

## Next (phase 1 to finish, needs Lef's OK)
- Restart one or two apps after the daemon is running, then read `active.json` while Lef focuses them.
- Measure CPU with AT-SPI always-on across a session.
- Then phase 2 (shell.json, with go-ahead) to see the widget.

## Second run (2026-11-07, 12:12, with Lef's go-ahead)
- Started the daemon first (`/usr/bin/python3`, transient unit), then opened a fresh LibreOffice Writer window, so the app started after the daemon. Focus was not moved by me. Sampled `active.json` every 3 s for 90 s.
- Result: LibreOffice Writer is `desktop-fallback` (File/Edit/View/Window/Help). Orca too. No real menu extracted.
- Stopped the daemon afterwards. `org.a11y.Status IsEnabled` read `false` after the stop, so the always-on effect ends with the daemon. `QT_LINUX_ACCESSIBILITY_ALWAYS_ON` is not set (the README's backup `environment.d` file is not installed).
- A Writer window opened by this test was left open for Lef to close.

## Conclusion for phase 1
- Verified: the daemon runs and tracks focus with the system Python; the earlier crash was the interpreter.
- Verified: in every app tried (7), only the generic fallback menu came back.
- Unknown: why no real menu is extracted (LibreOffice's accessibility tree, daemon extraction order, toolkit settings). Not diagnosed yet: I did not run `--debug` while a menu-bearing app was focused.
- Unknown: whether the widget renders (needs the `shell.json` edit, phase 2).
- Consequence: primo works as a shell, but real menus on this machine are not shown yet. This favours the fork idea (shortcut-profile fallback), but a fork is not decided until the extraction question is answered.
