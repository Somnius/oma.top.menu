# Everything the plugin does to your system

When each action happens, what it touches, and how to undo it. Nothing here runs at install time except starting the menu service.

## Always, while the plugin is enabled
| Action | Touches | Undo |
|---|---|---|
| The service starts one Python daemon (`/usr/bin/python3 bin/omarchy-global-menu-bridge --stream run`) | one process; a lock file `$XDG_RUNTIME_DIR/oma-top-menu.lock` | disable or remove the plugin (the daemon exits with its parent) |
| Reads window state: `hyprctl -j monitors/workspaces/clients/activewindow`, Hyprland socket2 events | read-only | none needed |
| Reads each window's menu: AT-SPI (accessibility bus), `org.gtk.Menus` and `com.canonical.dbusmenu` on the session bus; reads `.desktop` files in the standard XDG folders (name, icon, actions) | read-only | none needed |
| Registers an AT-SPI event listener and sets `org.a11y.Status IsEnabled` while running, so Qt and GTK4 apps expose their menus | the accessibility bus; every app's accessibility bridge stays on for the session | stop the daemon (disable the plugin): `IsEnabled` returns to false. Apps already running keep the bridge until restarted |
| Writes `active.json`, `request.json` (while a click is handled) and `status.json` | `$XDG_RUNTIME_DIR/oma-top-menu/` (tmpfs, cleared at logout) | disable the plugin; files vanish at logout; `bin/oma-top-menu-uninstall --apply` removes them now |
| Applies the focus-behaviour setting with `hyprctl eval` when you have chosen Hover, Click or Off in the panel, at startup and after a Hyprland config reload (verified 2026-11-07: with *System* a `hyprctl reload config-only` returned the value to 1, with *Click* it stayed at 2) | Hyprland's live setting only; **no file is written** | choose *System* in the panel, or remove the plugin; your own value returns at the next Hyprland reload |

## Only when you click
| Action | Touches | Undo |
|---|---|---|
| A menu entry | the app's own action over AT-SPI/D-Bus; for the generic menu: launches the app's `.desktop` command with `sh -c`, or runs a window operation with `hyprctl dispatch` (for example *Close Window*) | what the app did |
| Panel: Focus behaviour | the widget's `followMouse` setting in `shell.json` (through the shell's own settings call) and the live Hyprland value | choose *System* |
| Panel: Dividers, Spacing, App icon, Apps without a menu bar | the widget's settings in `shell.json` | choose the other option |
| Panel: Workspace numbers | runs `omarchy bar move omarchy.workspaces ...`, which edits the bar layout in `shell.json` | click another position (Left puts them just before the menu strip) |
| Panel: Position (Locked) | the widget's `locked` setting in `shell.json`; while locked the strip shows a transparent pointer area above itself in the bar window (no commands are run and nothing is moved) | choose *Free* |
| Panel: GitHub button | runs `xdg-open https://github.com/Somnius/oma.top.menu` | close the browser tab |
| Panel: Restart service (top of the editor) | restarts the daemon | none needed |
| Right-click on the strip or the icon: the editor; left-click on the icon: a read-only preview | opens a panel | Escape |

## Never
The plugin does not edit Hyprland config files, install packages, use `sudo` or `pkexec`, make network connections, or change anything outside the items above. Earlier builds (before 2026-11-07, evening) wrote `~/.local/state/omarchy/oma-top-menu` and, on a *Save* click, a marked block at the end of `~/.config/hypr/input.lua`; both are gone from the current design. If you used that Save button, remove the block with `bin/oma-top-menu-hypr-input follow_mouse --remove` (it makes a backup first).

## Removing the plugin
1. Optional but tidy: `bin/oma-top-menu-uninstall` (dry run) then `--apply`. It removes every bar entry for this plugin (Omarchy's own removal deletes only the first one; a leftover entry is harmless and draws nothing, tested), a legacy `input.lua` block and the state files, with a `shell.json` backup.
2. `omarchy plugin remove com.lefteros.somnius.oma-top-menu`.
After a plain `omarchy plugin remove` with no step 1: no process is left, nothing is drawn for a leftover entry, and nothing of ours remains on disk except that entry and, until logout, two small files in the runtime folder.
