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
- The menu daemon is restarted by the service after `kill -9` and after SIGTERM; after five quick exits in a row it stops and the bar shows a message.
- If python-gobject or AT-SPI is missing, the service says so in the bar instead of staying blank (logic present; not exercised by a real missing package).
- The daemon exits with its parent and removes its state files; a lock in `$XDG_RUNTIME_DIR` keeps a second copy from starting.

## Known risks
- A new Hyprland config format or renamed `follow_mouse` option would break the Focus behaviour control (the other controls would keep working). The saved block is plain Lua in `input.lua`, marked so it can be removed by hand.
- If Omarchy changes how widgets learn their section (`fixedEdge`), the icon-versus-menu rule would need a new signal.
- AT-SPI trees differ per toolkit and version; apps update independently of this plugin.
- `omarchy plugin add` installs the repository's current head, so what users get is whatever is on `main`.
