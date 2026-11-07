# Oma Top Menu

The focused app's menus (File, Edit, View...) on the left of the Omarchy top bar, like a macOS or GNOME global menu. The workspace numbers can sit on the right.

Plugin id: `com.lefteros.somnius.oma-top-menu` (codename `oma.top.menu`). Status: early work in progress, 0.1.0, not listed on the marketplace yet.

![Python 3](https://img.shields.io/badge/Python-3-3776AB?logo=python&logoColor=white)
![QML](https://img.shields.io/badge/QML-Quickshell-41CD52?logo=qt&logoColor=white)
![PyGObject](https://img.shields.io/badge/PyGObject-AT--SPI-4A86CF)
![Hyprland](https://img.shields.io/badge/Hyprland-compositor-58E1FF)
![Omarchy](https://img.shields.io/badge/Omarchy-plugin-7aa2f7)
![License](https://img.shields.io/badge/license-GPL--2.0-blue)

![Floorp](docs/screenshots/bar-floorp.png)
![Kotatogram](docs/screenshots/bar-kotatogram.png)
![Omamail](docs/screenshots/bar-omamail.png)
![An app with no menu bar of its own gets a generic menu](docs/screenshots/bar-fallback.png)

## What it does
- A bar widget shows the focused window's menu and lets you click through it.
- A background service (started by the plugin itself, one per shell) reads the menu from the app: `org.gtk.Menus`, `dbusmenu`, then the accessibility tree (AT-SPI). Apps without a menu bar of their own get a generic menu.
- Real menus come from apps that expose them. Sandboxed apps (whose accessibility pid differs from the window pid) are matched by name.

## Options panel
Add the widget a second time, on the right (next to the tray) or inside the tray drawer, and it becomes an options icon instead of the menu strip: where you place it decides what it is (the left section is the menu, anywhere else is the icon). The `shell.json` entry is just `{ "id": "com.lefteros.somnius.oma-top-menu" }` in `bar.layout.right`; `omarchy bar put` will not add a second copy, so add it by hand or drag it in the bar editor.

![Options panel](docs/screenshots/options-panel.png)

Supported places: the left section for the menu, and the right section or the tray drawer for the icon. The bar tells a widget only a layout hint, not its section, so other places (the centre sections) are not supported.

- **Focus behaviour**: Hover / Click / Off. It applies at once with `hyprctl eval`; *Save* writes a small marked block at the end of `~/.config/hypr/input.lua` (a timestamped backup first). Nothing is changed until you click.
- **Workspace numbers**: Left (just before the menu), Middle or Right (the start of that section), done with `omarchy bar move omarchy.workspaces --section ...`.
- **Dividers**, **Spacing** (compact, normal, roomy), **App icon**, **Apps without a menu bar** (generic menu or nothing). The workspace move edits your `shell.json` through Omarchy's own `omarchy bar move`, only when you click it. These are the widget's settings in `shell.json`, shared by the menu strip and the icon.
- **Restart menu service**.

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
Run `bin/oma-top-menu-uninstall` first (it shows what it would clean; `--apply` does it). Omarchy's own removal leaves the options-icon entry, the saved `input.lua` block and the state folder behind. Then:

Take `com.lefteros.somnius.oma-top-menu` out of `~/.config/omarchy/shell.json`, then `omarchy plugin remove com.lefteros.somnius.oma-top-menu` (or delete `~/.config/omarchy/plugins/com.lefteros.somnius.oma-top-menu`). The service stops with the plugin and removes its files in `~/.local/state/omarchy/oma-top-menu`.

## Recommended: focus on click, not on hover
Omarchy's default is `follow_mouse = 1` (the cursor always changes focus). With it, moving the pointer up to the bar crosses other windows and the menu switches to them before you can click it. Set Hyprland to move keyboard focus only when you click:

```lua
-- ~/.config/hypr/input.lua
hl.config({
  input = {
    follow_mouse = 2,  -- 0: cursor never changes focus, 1: always (Omarchy default),
                       -- 2: click to focus, 3: click does not even change keyboard focus
  },
})
```
The plugin never changes your Hyprland config. (Values from the Hyprland wiki.)

## Side effect to know about
To get menus out of Qt and GTK4 apps, the service registers an AT-SPI listener, which turns accessibility on for the whole session while it runs (`org.a11y.Status IsEnabled` becomes true). It goes back when the service stops. The cost of that is not measured yet.

## Updates and compatibility
Tested on Omarchy 4.5.0-3 with Hyprland 0.56.2. See [docs/compatibility.md](docs/compatibility.md) for what the plugin depends on, how plugin updates behave, and the checks to run after an Omarchy update (`python3 tests/check_shell_api.py`).

## Known limits
- Firefox-family browsers (tested: Floorp) only fill a menu after it has been opened once, so some entries are empty at first and a click opens the menu inside the app. The menus you have already opened show up in the bar.
- Apps that were already running before the service started keep an empty accessibility tree until restarted.
- Apps with no menu bar (terminals, many GTK4 apps) get the generic menu.

## Credits
Based on [primo.global-menu](https://github.com/PrimoGameStudio/primo.global-menu) by PrimoGameStudio (GPL-2.0). Inspired by the Global Menu GNOME extension by [Unmade760](https://github.com/Unmade760/orbit-global-menu).

Built with Claude Code; JEV (TypeSafe) was used to classify the marketplace catalog.

## License
GPL-2.0, see [LICENSE](LICENSE).

## Docs
[SPECS.md](SPECS.md), [ROADMAP.md](ROADMAP.md), [AGENTS.md](AGENTS.md), [NOTES.md](NOTES.md), [docs/](docs).
