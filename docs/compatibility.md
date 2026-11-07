# Compatibility and updates

Tested on: Omarchy 4.5.0-3, Hyprland 0.56.2 (Lua config), Quickshell, Python 3.14 (system), python-gobject 3.58.1, at-spi2-core 2.62.1, 2026-11-07.

## Updating the plugin itself (tested)
`omarchy plugin update` does `git fetch`, `merge --ff-only`, then `omarchy-plugin-validate`, and rolls back if validation fails. Tested in a throwaway home: from an older commit of this repo to the current head, it fast-forwarded, validated and left the tree clean, and running the bridge from the clone did not dirty it. The plugin never writes into its own folder (state and the lock go to `$XDG_RUNTIME_DIR/oma-top-menu`, which is tmpfs), so updates keep working. User settings live in `shell.json`, not in the plugin folder, so they survive an update.

## What the plugin depends on in Omarchy (the contract)
Shell pieces: `qs.Ui` (BarWidget, Panel, KeyboardPanel, PanelKeyCatcher, PanelSectionHeader, ButtonGroup, Button, WidgetButton, BorderSurface), `qs.Commons` (Style, Color, Util), the bar facade (`requestPopout`, `releasePopout`, `activePopout`, `switchPanelFrom`, `shell.serviceFor`, `shell.updateEntryInline`), the widget properties `fixedEdge`, `settings`, `moduleName`, and the manifest keys `kinds`, `entryPoints`, `barWidget.defaults`, `barWidget.schema`, `allowMultiple`.
Commands: `omarchy bar move omarchy.workspaces --before|--section ... --index`, `hyprctl getoption/eval/dispatch`, `/usr/bin/python3`.
Not part of Omarchy's documented plugin reference as far as I checked: the bar facade members and `fixedEdge`; they are used by Omarchy's own widgets, so they are the most likely to change.

## After an Omarchy, Hyprland or Python update
Run `python3 tests/check_shell_api.py` (greps the installed shell for every name above and runs the two commands) and `python3 -m unittest discover -s tests`. CI runs the unit tests, a compile check and a manifest check on every push.

## Failure handling (tested)
- The menu daemon is restarted by the service after `kill -9` and after SIGTERM (both tested on 2026-11-07); after six quick exits in a row it stops and the bar shows a message.
- If python-gobject or AT-SPI is missing, the service says so in the bar instead of staying blank (logic present; not exercised by a real missing package).
- The daemon checks its parent every loop and exits when it changes (tested by killing the parent), and on SIGTERM it removes `active.json` and `request.json` (`status.json` and the folder stay, `bin/oma-top-menu-uninstall` removes them). A lock in `$XDG_RUNTIME_DIR` keeps a second copy from starting.

## Removing the plugin
`omarchy plugin remove` disables the plugin and deletes its folder, but Omarchy's disable deletes only the first bar entry with the plugin id, so the options-icon copy would stay in `shell.json`; nothing is written to Hyprland files by the current design (older builds wrote an `input.lua` block, which the helper also removes), and the runtime state folder is cleared at logout. Run `bin/oma-top-menu-uninstall` first (dry run by default, `--apply` to clean, with a `shell.json` backup), then `omarchy plugin remove`. Tested against a temp config. What the bar draws for an entry whose plugin is gone is not verified.

## Multi-monitor (tested 2026-11-07 with a virtual monitor)
`hyprctl output create headless` added a second monitor; the bar on it showed its own menu (Files) while the first showed another (Omamail/Kotatogram), also while focus moved between monitors; closing the window cleared that monitor's menu; removing the monitor returned to normal; one daemon throughout; idle CPU about 0.6%. Unit tests cover the monitor planning (focused, other, empty, stale `lastwindow`, special workspace, shell popup).

Two windows of one app, tested live (2026-11-07): a second Floorp window was opened on the virtual monitor (workspace 31) while the first stayed on `DP-3`; the diagnostic showed each Hyprland window resolving to the menu bar inside its own window frame (the frame whose name is that window's title), and the virtual monitor's bar showed Floorp's real menus. A menu entry activated from the virtual monitor's snapshot while `DP-3` had focus ran without error and did not move focus; whether Floorp opened its in-app menu was not visible. Chromium (no menu bar of its own, so the generic menu) with 1, 2 and 3 windows on workspace 4, using an isolated profile: the bar's snapshot followed the focused window every time (4 of 4), idle CPU about 0.1%. Not tested: a real second physical monitor.

## Position lock (tested 2026-11-07)
With the lock on, moving the menu to `centerBegin` with `omarchy bar move` was undone within about 2 s (also right after a shell start with the lock already saved); with it off the move stayed. A start-up bug found on 2026-11-07 (copies of the widget that had not received their settings yet reported "not locked" and switched the lock off, so the lock could be lost after a restart) is fixed: only the menu strip reports, and only after the bar has assigned its settings; three consecutive shell restarts all came up locked. The lock relies on `omarchy bar move --index` and on reading `shell.json`; if either changes it stops working and nothing else is affected. See docs/moving-the-menu.md.

## Removal (tested 2026-11-07)
Disable, move the folder aside and restart the shell with both bar entries present: no process left, no journal errors, nothing drawn for the leftover entry; the second entry stays in `shell.json` (Omarchy deletes only the first). State is in the runtime folder (tmpfs), and nothing is written to Hyprland files. Everything was restored byte-for-byte afterwards.

## Not covered by tests
CI (Python 3.12) runs a compile check, a manifest check and unit tests of pure functions only: no Hyprland, QML, AT-SPI or PyGObject. `tests/check_shell_api.py` checks that names exist and two commands run; it cannot detect a changed signature or changed behaviour. The update, restart and kill tests above were run by hand, not automated. A change in at-spi2-core's accessibility semantics would silently fall back to the generic menu; there is no self-check for that yet.

## Known risks
- A renamed `follow_mouse` option or a changed `hyprctl eval` would break the Focus behaviour control only (the other controls keep working). Nothing is written to Hyprland files, so a failure leaves your config untouched.
- If Omarchy changes how widgets learn their section (`fixedEdge`), the icon-versus-menu rule would need a new signal.
- AT-SPI trees differ per toolkit and version; apps update independently of this plugin.
- `omarchy plugin add` installs the repository's current head, so what users get is whatever is on `main`.
