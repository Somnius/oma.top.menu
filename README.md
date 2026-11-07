# Oma Top Menu

The focused app's menus (File, Edit, View...) on the left of the Omarchy top bar, like a macOS or GNOME global menu. The workspace numbers can sit on the right.

Plugin id: `com.lefteros.somnius.oma-top-menu` (codename `oma.top.menu`). Status: early work in progress, 0.1.0, not listed on the marketplace yet.

<!-- TECH-STACK PILLS: to be added when Lef supplies them (see ROADMAP.md) -->

## What it does
- A bar widget shows the focused window's menu and lets you click through it.
- A background service (started by the plugin itself, one per shell) reads the menu from the app: `org.gtk.Menus`, `dbusmenu`, then the accessibility tree (AT-SPI). Apps without a menu bar of their own get a generic menu.
- Real menus come from apps that expose them. Sandboxed apps (whose accessibility pid differs from the window pid) are matched by name.

## Requirements
- Omarchy with the Quattro shell, Hyprland.
- `python-gobject` and `at-spi2-core` (the plugin checks for them and says so in the bar if they're missing): `sudo pacman -S python-gobject`.
- It uses `/usr/bin/python3`.

## Install
```
omarchy plugin add https://github.com/Somnius/oma.top.menu
```
Then add the widget to the left side of your bar. To also move the workspace numbers to the right, edit `~/.config/omarchy/shell.json`: take `omarchy.workspaces` out of `bar.layout.left` and put it in `bar.layout.right`. The plugin never edits `shell.json` for you.

## Remove
Take `com.lefteros.somnius.oma-top-menu` out of `~/.config/omarchy/shell.json`, then `omarchy plugin remove com.lefteros.somnius.oma-top-menu` (or delete `~/.config/omarchy/plugins/com.lefteros.somnius.oma-top-menu`). The service stops with the plugin and removes its files in `~/.local/state/omarchy/oma-top-menu`.

## Side effect to know about
To get menus out of Qt and GTK4 apps, the service registers an AT-SPI listener, which turns accessibility on for the whole session while it runs (`org.a11y.Status IsEnabled` becomes true). It goes back when the service stops. The cost of that is not measured yet.

## Known limits
- Apps that were already running before the service started keep an empty accessibility tree until restarted.
- Apps with no menu bar (terminals, many GTK4 apps) get the generic menu.

## Credits
Based on [primo.global-menu](https://github.com/PrimoGameStudio/primo.global-menu) by PrimoGameStudio (GPL-2.0). Inspired by the Global Menu GNOME extension by [Unmade760](https://github.com/Unmade760/orbit-global-menu).

Built with Claude Code; JEV (TypeSafe) was used to classify the marketplace catalog.

## License
GPL-2.0, see [LICENSE](LICENSE).

## Docs
[SPECS.md](SPECS.md), [ROADMAP.md](ROADMAP.md), [AGENTS.md](AGENTS.md), [NOTES.md](NOTES.md), [docs/](docs).
