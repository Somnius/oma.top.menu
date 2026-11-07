# Compatibility and updates

Tested on: Omarchy 4.5.0-3, Hyprland 0.56.2 (Lua config), Quickshell, Python 3.14 (system), python-gobject 3.58.1, at-spi2-core 2.62.1, 2026-11-07.

## Updating the plugin itself (tested)
`omarchy plugin update` does `git fetch`, `merge --ff-only`, then `omarchy-plugin-validate`, and rolls back if validation fails. Tested in a throwaway home: from an older commit of this repo to the current head, it fast-forwarded, validated and left the tree clean, and running the bridge from the clone did not dirty it. The plugin never writes into its own folder (state goes to `~/.local/state/omarchy/oma-top-menu`, the runtime lock to `$XDG_RUNTIME_DIR`), so updates keep working. User settings live in `shell.json`, not in the plugin folder, so they survive an update.

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
`omarchy plugin remove` disables the plugin and deletes its folder, but Omarchy's disable deletes only the first bar entry with the plugin id, so the options-icon copy would stay in `shell.json`; the saved `input.lua` block and the state folder also stay. Run `bin/oma-top-menu-uninstall` first (dry run by default, `--apply` to clean, with a `shell.json` backup), then `omarchy plugin remove`. Tested against a temp config. What the bar draws for an entry whose plugin is gone is not verified.

## Multi-monitor (tested 2026-11-07 with a virtual monitor)
`hyprctl output create headless` added a second monitor; the bar on it showed its own menu (Files) while the first showed another (Omamail/Kotatogram), also while focus moved between monitors; closing the window cleared that monitor's menu; removing the monitor returned to normal; one daemon throughout; idle CPU about 0.6%. Unit tests cover the monitor planning (focused, other, empty, stale `lastwindow`, special workspace, shell popup). Not tested: two windows of one app on two monitors (matching by frame title is unit-tested with stub accessibles only), clicking a menu item on a monitor that does not have focus, and a real second physical monitor.

## Removal (tested 2026-11-07)
Disable, move the folder aside and restart the shell with both bar entries present: no process left, no journal errors, nothing drawn for the leftover entry; the second entry stays in `shell.json` (Omarchy deletes only the first). State is in the runtime folder (tmpfs), and nothing is written to Hyprland files. Everything was restored byte-for-byte afterwards.

## Not covered by tests
CI (Python 3.12) runs a compile check, a manifest check and unit tests of pure functions only: no Hyprland, QML, AT-SPI or PyGObject. `tests/check_shell_api.py` checks that names exist and two commands run; it cannot detect a changed signature or changed behaviour. The update, restart and kill tests above were run by hand, not automated. A change in at-spi2-core's accessibility semantics would silently fall back to the generic menu; there is no self-check for that yet.

## Known risks
- A renamed `follow_mouse` option or a changed `hyprctl eval` would break the Focus behaviour control only (the other controls keep working). Nothing is written to Hyprland files, so a failure leaves your config untouched.
- If Omarchy changes how widgets learn their section (`fixedEdge`), the icon-versus-menu rule would need a new signal.
- AT-SPI trees differ per toolkit and version; apps update independently of this plugin.
- `omarchy plugin add` installs the repository's current head, so what users get is whatever is on `main`.
