# Options icon (draft for review)

Request (Lef): an Oma Top Menu icon in the right-hand area of the bar, next to the tray / hidden-apps icons, that opens a panel with the plugin's options, for example the recommendation to switch off focus-follows-mouse.

## Verified facts (Omarchy shell source and local tests, 2026-11-07)
- A manifest has one `barWidget` entry point. `barWidget.allowMultiple`, `defaults` and a typed `schema` (enum/string fields with labels) are supported; `allowMultiple` is read in `shell.qml:1470`.
- Each widget instance gets `moduleName` and `settings` injected by the bar (`Bar.qml` `injectProps`, `settings = entrySettings(entry)` from its shell.json entry).
- Widgets save settings with `bar.shell.updateEntryInline(moduleName, entry)` (clock `Panel.qml` `persistSettings`); the write comes back through the bar.
- `hyprctl eval '<lua>'` runs Lua config at runtime. `hyprctl eval 'hl.config({ input = { follow_mouse = 1 } })'` printed `ok` and left the value at 1 (a no-op test).
- Omarchy's default is `follow_mouse = 1`; the user's overrides file is `~/.config/hypr/input.lua` (a `hl.config({ input = { ... } })` block with comments).
- `follow_mouse`: 0 never changes focus, 1 always, 2 click moves keyboard focus, 3 click does not (Hyprland wiki).

## Unknown, needs a test
- How a second instance of the same widget id is keyed (`moduleName`) and whether `updateEntryInline` can address each instance separately.
- Whether `omarchy plugin enable` or the bar editor can place a second entry (`{"id": "...", "role": "options"}`) in `bar.layout.right`.
- Whether there is a supported way to put a widget into the tray/overflow area, or only into the `right` section next to it.

## Added requests (Lef, 2026-11-07)
- Workspace numbers: choose left, middle or right.
- Dividers between menu entries: shown or hidden.
- Spacing: smaller or larger (compact, normal, roomy).

Extra verified facts:
- Bar sections are `left`, `centerBegin`, `center`, `centerEnd`, `right` (`Bar.qml`). The bar already supports dragging a widget between sections.
- The plugin-facing shell API (`services/PluginShellApi.qml`) exposes `mutateShellConfig(mutator)`, backed by `shell.mutatePluginBarConfig` and gated by `hasCurrentBarCapabilities()`; the bar itself uses `BarModel.moveEntry(config, move, ...)` inside `mutateShellConfig` to move an entry. Unknown: whether a plugin may move another widget's entry (`omarchy.workspaces`), and the exact `move` object format.

## Proposed design
1. Same plugin, `allowMultiple: true`, new schema field `role` (enum `menu` | `options`, default `menu`). Role `options` renders only an icon button (our own SVG, `assets/icon.svg`, themed with the bar foreground) that opens a panel; role `menu` is today's strip.
2. If a second instance cannot be keyed per entry: fall back to a small gear at the left end of the menu strip, or a second tiny plugin. Decide after the test.
3. Panel contents, v1:
   - Status: daemon running or error (from the service), focused app, menu source (at-spi / fallback).
   - Focus behaviour: segmented control Hover (1) / Click (2) / Off (0), showing the live value from `hyprctl getoption input:follow_mouse`. Choosing applies live with `hyprctl eval` (a change Lef asks for by clicking). A separate button "Save to ~/.config/hypr/input.lua" writes the line with a timestamped backup and shows the exact change first. The plugin never edits Hyprland config without that click (marketplace checklist: no overwriting user config without explicit consent).
   - Workspace numbers: Left / Middle / Right, applied by moving the `omarchy.workspaces` entry through `mutateShellConfig` (only on click; the bar's own drag-and-drop does the same thing).
   - Dividers between menu entries: Show / Hide (a setting read by the widget).
   - Spacing: Compact / Normal / Roomy (a setting that scales the entry padding).
   - Show app icon (on/off), Show generic menu for apps without a menu bar (on/off), Restart daemon.
4. Settings live in the widget's shell.json entry (`defaults` + `schema`), so Omarchy's own bar settings editor also lists them.
5. The README documents the panel; screenshots added.

## Risks to check in review
- `hyprctl eval` of a string built in QML: injection (values are fixed integers from an enum, never free text).
- Editing `input.lua` programmatically: robustness against the user's comments and formatting; must be an explicit action with a backup; must not break a hand-edited file.
- A second widget instance must not start a second daemon (it doesn't: the service owns it) or double-register IPC (`IpcHandler target` in `BarWidget.qml` would be registered per instance).

## Review results (two independent reviews) and decision, 2026-11-07
- Two instances of the same widget id share one settings record: `updateEntryInline` rewrites every entry with that id, and `moduleName` is just the id. So a per-entry `role` setting cannot work.
- `allowMultiple` is only copied into registry metadata; whether the bar editor enforces it is unknown. The CLI `omarchy bar put <id> --section <s>` exists and can be tried.
- There is no overflow area. The tray drawer is a `tray` section for StatusNotifier icons; widgets go in `right` (next to the tray) or can be dragged into `tray`.
- A plugin can move another widget's entry through `mutateShellConfig` only if its manifest kinds include `bar` (full bar replacement), which we are not. But the supported CLI does it: `omarchy bar move omarchy.workspaces --section <left|centerBegin|center|centerEnd|right> [--index N]`; `omarchy bar set <id> <key> <value>` writes widget settings.
- Widgets receive `fixedEdge` from the bar: "start" in the left section, "end" in the right section, "center" in the middle (`Ui/BarWidget.qml`, `Bar.qml`).

Decision: one widget, `allowMultiple: true`; its role comes from where it is placed, not from a setting. Placed in the left section (`fixedEdge` "start") it is the menu strip; placed in the right section (`fixedEdge` "end") it is the options icon. Both read the same shared settings (dividers, spacing, show icon), which is what we want. If the bar refuses a second entry, fall back to a gear at the left end of the strip.
Workspace position uses `omarchy bar move omarchy.workspaces --section ...`, run from a button the user clicks. Hyprland `follow_mouse` uses `hyprctl eval` for the live change and an explicit, backed-up edit of `~/.config/hypr/input.lua` for saving.
Panel built from Omarchy's own UI pieces (`Ui/Panel`, `KeyboardPanel`, `ButtonGroup`, `PanelSlider`, `BarIconButton`), icon `assets/icon.svg`.
